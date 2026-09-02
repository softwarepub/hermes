# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Union
from typing_extensions import Self

from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import BASIC_TYPE, JSON_LD_VALUE, TIME_TYPE

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
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]:
        """
        An abstract method that needs to be implemented by all subclasses
        to have a generic way to use the merge actions.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent ``out_parent[key[0]]...[key[-1]]`` results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target``
                with ``value``.

        Returns:
            JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list:
                The merged value in an arbitrary format that is supported by :meth:`ld_dict.__setitem__`.
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        """
        A generic stringify method for MergeActions.
        Please overwrite this method if your MergeAction should be represented differently in the provenance data.
        (I.e. if not all important attributes are recorded or some attributes string representation is not adequat.)
        """
        if self.__dict__:
            return f"{self.__module__}.{self.__class__.__qualname__} with attributes {str(self.__dict__)}"
        return f"{self.__module__}.{self.__class__.__qualname__}"


class Reject(MergeAction):
    """ :class:`MergeAction` providing a merge function for rejecting the incoming item. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Rejects the new data ``update`` and lets ``target`` add an entry to itself
        documenting what data has been rejected.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent ``out_parent[key[0]]...[key[-1]]`` results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
                This value won't be changed.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target`` with
                ``value``. This value will be rejected.

        Returns:
            ld_merge_list | str: The merged value. This value will always be ``value``.
        """
        if value != update:
            # Add the entry that data has been rejected.
            target.reject(key, update)
        # Return value unchanged.
        return value


class Replace(MergeAction):
    """ :class:`MergeAction` providing a merge function for replacing the current item with the incoming one. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]:
        """
        Replaces the old data ``value`` with the new data ``update``
        and lets ``target`` add an entry to itself documenting what data has been replaced.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent ``out_parent[key[0]]...[key[-1]]`` results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
                This value will bew replaced.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target`` with
                ``value``. This value will be used instead of ``value``.

        Returns:
            BASIC_TYPE | TIME_TYPE | ld_dict | ld_list: The merged value. This value will be ``update``.
        """
        if value != update:
            # Add the entry that data has been replaced.
            target.replace(key, value)
        # Return the new value.
        return update


class Concat(MergeAction):
    """ :class:`MergeAction` providing a merge function for appending the incoming items to the current items. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Concatenates the new data ``update`` to the old data ``value``.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent ``out_parent[key[0]]...[key[-1]]`` results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target``
                with ``value``.

        Returns:
            ld_merge_list | str: The merged value (``value`` concatenated with ``update``).
        """
        # Concatenate the items and return the result.
        if isinstance(update, (list, ld_list)):
            value.extend(update)
        else:
            value.append(update)
        return value


class Collect(MergeAction):
    """
    :class:`MergeAction` providing a merge function for appending the incoming items to the current items. But an item
    will only be appended if it has no match in the list of current items (including the already appended ones).

    Attributes:
        match (Callable[[Any, Any], bool]): The function used to evaluate equality while merging.
        reject_incoming (bool): Whether the incoming item in a match should get rejected (True) or replaced (False).
    """

    def __init__(self: Self, match: Callable[[Any, Any], bool], reject_incoming: bool = True) -> None:
        """
        Set the match function for this collect merge action. And the behaivior for matches.

        Args:
            match (Callable[[Any, Any], bool]): The function used to evaluate equality while merging.
            reject_incoming (bool): If an incoming item matches an already collected one, if ``reject_incoming`` True,
                the incoming item gets rejected, if ``reject_incoming`` False, the match of the incoming item gets
                replaced.

        Returns:
            None:
        """
        self.match = match
        self.reject_incoming = reject_incoming

    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Collects the unique items (according to :attr:`match`) from ``value`` and ``update``.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent ``out_parent[key[0]]...[key[-1]]`` results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target``
                with ``value``.

        Returns:
            ld_merge_list | str: The merged value.
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

    def __repr__(self):
        return f"{self.__module__}.{self.__class__.__qualname__} with attributes " \
            f"{{'match': {self.match.__module__}.{self.match.__qualname__}, 'reject_incoming': {self.reject_incoming}}}"


class MergeSet(MergeAction):
    """
    :class:`MergeAction` providing a merge function for merging the incoming items with the current items. An item
    will be appended if it has no match in the list of current items (including the already appended ones), otherwise
    it will be merged with its first match.

    Attributes:
        match (Callable[[Any, Any], bool]): The function used to evaluate equality while merging.
    """

    def __init__(self: Self, match: Callable[[Any, Any], bool]) -> None:
        """
        Set the match function for this collect merge action.

        Args:
            match (Callable[[Any, Any], bool]): The function used to evaluate equality while merging.

        Returns:
            None:
        """
        self.match = match
        """ Callable[[Any, Any], bool]: The function used to evaluate equality while merging. """

    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Merges similar items (according to :attr:`match`) from ``value`` and ``update``.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent out_parent[key[0]]...[key[-1]] results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target``
                with ``value``.

        Returns:
            ld_merge_list | str: The merged value.
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
                        """
                        FIXME: log error/ warning that merge of items at... could not be merged and will be skipped
                        """
                    break
            else:
                value.append(update_item)
        # Return the merged values.
        return value

    def __repr__(self):
        return f"{self.__module__}.{self.__class__.__qualname__} with attributes " \
            f"{{'match': {self.match.__module__}.{self.match.__qualname__}}}"


class IdMerge(MergeAction):
    """ :class:`MergeAction` providing a merge function for merging ids, i.e. error if not equals else do nothing. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        """
        Error if value != update or key != "@id". Else do nothing.

        Args:
            target (ld_merge_dict): The ld_merge_dict inside of which the items are merged.
            key (list[str | int]): The "path" of keys so that ``target[key[-1]]`` is ``value`` and for the outermost
                parent of ``target`` out_parent out_parent[key[0]]...[key[-1]] results in ``value``.
            value (ld_merge_list | str): The value inside ``target`` that is to be merged with ``update``.
            update (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged into ``target``
                with ``value``.

        Returns:
            ld_merge_list | str: The merged value.
        """
        if key[-1] != "@id":
            raise MergeError("Can't merge non-'@id' values.")
        if value != update:
            raise MergeError("Two different '@id' values are merged into the same object.")
        return value
