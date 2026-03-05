# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Union
from typing_extensions import Self

from ..types import ld_dict, ld_list
from ..types.ld_container import BASIC_TYPE, JSON_LD_VALUE, TIME_TYPE

if TYPE_CHECKING:
    from .container import ld_merge_dict, ld_merge_list


class MergeError(ValueError):
    """ Class for any error while merging. """
    pass


class MergeAction:
    """ Base class for the different actions occuring druing a merge. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]:
        """
        An abstract method that needs to be implemented by all subclasses
        to have a generic way to use the merge actions.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value in an arbitrary format that is supported by :meth:`ld_dict.__setitem__`.
        :rtype: JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list
        """
        raise NotImplementedError()


class Reject(MergeAction):
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Rejects the new data ``update`` and lets target add an entry to itself documenting what data has been rejected.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.<br> This value won't be changed.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.<br> This value will be rejected.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value.<br>
            This value will always be value.
        :rtype: ld_merge_list
        """
        # Add the entry that data has been rejected.
        target.reject(key, update)
        # Return value unchanged.
        return value


class Replace(MergeAction):
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]:
        """
        Replaces the old data ``value`` with the new data ``update``
        and lets target add an entry to itself documenting what data has been replaced.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.<br> This value will bew replaced.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.<br>
            This value will be used instead of value.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value.<br>
            This value will be update.
        :rtype: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list
        """
        # If necessary, add the entry that data has been replaced.
        target.replace(key, value)
        # Return the new value.
        return update


class Concat(MergeAction):
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Concatenates the new data ``update`` to the old data ``value``.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value.<br>
            ``value`` concatenated with ``update``.
        :rtype: ld_merge_list
        """
        # Concatenate the items and return the result.
        if isinstance(update, (list, ld_list)):
            value.extend(update)
        else:
            value.append(update)
        return value


class Collect(MergeAction):
    def __init__(self: Self, match: Callable[[Any, Any], bool], reject_incoming: bool = True) -> None:
        """
        Set the match function for this collect merge action. And the behaivior for matches.

        :param match: The function used to evaluate equality while merging.
        :type match: Callable[[Any, Any], bool]
        :param reject_incoming: If an incoming item matches an already collected one, if ``reject_incoming`` True,
            the incoming item gets rejected, if ``reject_incoming`` False, the match of the incoming item gets replaced.
        :type reject_incoming: bool

        :return:
        :rtype: None
        """
        self.match = match
        self.reject_incoming = reject_incoming

    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Collects the unique items (according to :attr:`match`) from ``value`` and ``update``.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value.
        :rtype: ld_merge_list
        """
        if not isinstance(update, (list, ld_list)):
            update = [update]

        # iterate over all new items
        for update_item in update:
            # Iterate over all items in value and if a match is found replace the first one or reject update_item.
            for index, item in enumerate(value):
                if self.match(item, update_item):
                    if not self.reject_incoming:
                        value[index] = update_item
                    break
            else:
                # If the current new item has no occurence in value (according to self.match) add it to value.
                value.append(update_item)

        return value


class MergeSet(MergeAction):
    def __init__(self: Self, match: Callable[[Any, Any], bool]) -> None:
        """
        Set the match function for this collect merge action.

        :param match: The function used to evaluate equality while merging.
        :type match: Callable[[ANy, Any], bool]

        :return:
        :rtype: None
        """
        self.match = match

    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: ld_merge_list,
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Merges similar items (according to :attr:`match`) from ``value`` and ``update``.

        :param target: The ld_merge_dict inside of which the items are merged.
        :type target: ld_merge_dict
        :param key: The "path" of keys so that parent[key[-1]] is value and
            for the outermost parent of target out_parent out_parent[key[0]]...[key[-1]] results in value.
        :type key: list[str | int]
        :param value: The value inside target that is to be merged with update.
        :type value: ld_merge_list
        :param update: The value that is to be merged into target with value.
        :type update: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The merged value.
        :rtype: ld_merge_list
        """
        if not isinstance(update, (list, ld_list)):
            update = [update]

        for update_item in update:
            # For each new item merge it into a similar item (according to match) inside target[key[-1]]
            # (aka inside value) if such an item exists.
            # Otherwise append it to target[key[-1]] (aka to value).
            for index, item in enumerate(value):
                if self.match(item, update_item):
                    if isinstance(item, ld_dict) and isinstance(update_item, ld_dict):
                        item.update(update_item)
                    elif isinstance(item, ld_list) and isinstance(update_item, ld_list):
                        self.merge(target, [*key, index], item, update_item)
                    elif isinstance(item, (ld_dict,  ld_list)) or isinstance(update_item, (ld_dict, ld_list)):
                        """ FIXME: log error """
                    break
            else:
                value.append(item)
        # Return the merged values.
        return value
