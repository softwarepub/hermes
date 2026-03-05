# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Union
from typing_extensions import Self

from ..types import ld_container, ld_context, ld_dict, ld_list
from ..types.ld_container import (
    BASIC_TYPE, EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT, JSON_LD_VALUE, TIME_TYPE
)
from ..types.pyld_util import bundled_loader
from .strategy import CODEMETA_STRATEGY, PROV_STRATEGY

if TYPE_CHECKING:
    from .action import MergeAction


class _ld_merge_container:
    """
    Abstract base class for ld_merge_dict and ld_merge_list,
    providing the merge containers with overrides of ld_container._to_python().
    See also :class:`ld_dict`, :class:`ld_list` and :class:`ld_container`.
    """

    def _to_python(
        self: Self,
        full_iri: str,
        ld_value: Union[EXPANDED_JSON_LD_VALUE, dict[str, EXPANDED_JSON_LD_VALUE], list[str], str]
    ) -> Union["ld_merge_dict", "ld_merge_list", BASIC_TYPE, TIME_TYPE]:
        """
        Returns a pythonized version of the given value pretending the value is in self and full_iri its key.

        :param self: the ld_container ld_value is considered to be in.
        :type self: Self
        :param full_iri: The expanded iri of the key of ld_value / self (later if self is not a dictionary).
        :type full_iri: str
        :param ld_value: The value thats pythonized value is requested. ld_value has to be valid expanded JSON-LD if it
            was embeded in self._data.
        :type ld_value: EXPANDED_JSON_LD_VALUE | dict[str, EXPANDED_JSON_LD_VALUE] | list[str] | str

        :return: The pythonized value of the ld_value.
        :rtype: ld_merge_dict | ld_merge_list | BASIC_TYPE | TIME_TYPE
        """
        value = super()._to_python(full_iri, ld_value)
        # replace ld_dicts with ld_merge_dicts
        if isinstance(value, ld_dict) and not isinstance(value, ld_merge_dict):
            value = ld_merge_dict(
                value.ld_value,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context
            )
        # replace ld_lists with ld_merge_lists
        if isinstance(value, ld_list) and not isinstance(value, ld_merge_list):
            value = ld_merge_list(
                value.ld_value,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context
            )
        return value


class ld_merge_list(_ld_merge_container, ld_list):
    """
    ld_list wrapper to ensure the 'merge_container'-property does not get lost, while merging.
    See also :class:`ld_list` and :class:`ld_merge_container`.
    """

    def __init__(
        self: "ld_merge_list",
        data: Union[list[str], list[dict[str, EXPANDED_JSON_LD_VALUE]]],
        *,
        parent: Union[ld_container, None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None
    ) -> None:
        """
        Create a new ld_merge_list.
        For further information on this function and the errors it throws see :meth:`ld_list.__init__`.

        :param self: The instance of ld_merge_list to be initialized.
        :type self: Self
        :param data: The expanded json-ld data that is mapped (must be valid for @set, @list or @graph)
        :type data: list[str] | list[dict[str, BASIC_TYPE | EXPANDED_JSON_LD_VALUE]]
        :param parent: parent node of this container.
        :type parent: ld_container | None
        :param key: key into the parent container.
        :type key: str | None
        :param index: index into the parent container.
        :type index: int | None
        :param context: local context for this container.
        :type context: list[str | JSON_LD_CONTEXT_DICT] | None

        :return:
        :rtype: None
        """
        super().__init__(data, parent=parent, key=key, index=index, context=context)


class ld_merge_dict(_ld_merge_container, ld_dict):
    """
    ld_dict wrapper providing methods to merge an object of this class with an ld_dict object.
    See also :class:`ld_dict` and :class:`ld_merge_container`.

    :ivar strategies: The strategies for merging different types of values in the ld_dicts.
    :ivartype strategies: dict[str | None, dict[str | None, MergeAction]]
    """

    def __init__(
        self: Self,
        data: list[dict[str, EXPANDED_JSON_LD_VALUE]],
        *,
        parent: Union[ld_dict, ld_list, None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None
    ) -> None:
        """
        Create a new instance of an ld_merge_dict.
        See also :meth:`ld_dict.__init__`.

        :param self: The instance of ld_container to be initialized.
        :type self: Self
        :param data: The expanded json-ld data that is mapped.
        :type data: EXPANDED_JSON_LD_VALUE
        :param parent: parent node of this container.
        :type parent: ld_dict | ld_list | None
        :param key: key into the parent container.
        :type key: str | None
        :param index: index into the parent container.
        :type index: int | None
        :param context: local context for this container.
        :type context: list[str | JSON_LD_CONTEXT_DICT] | None

        :return:
        :rtype: None

        :raises ValueError: If the given data doesn't represent an ld_dict.
        """
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        # add provernance context
        self.update_context(ld_context.HERMES_PROV_CONTEXT)

        # add strategies
        self.strategies = {**CODEMETA_STRATEGY}
        self.add_strategy(PROV_STRATEGY)

    def update_context(
        self: Self, other_context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None]
    ) -> None:
        """
        Updates selfs context with other_context.
        JSON-LD processing prioritizes the context values in order (first least important, last most important).

        :param self: The instance of the ld_merge_dict context is added to.
        :type self: Self
        :param other_context: The context object that is added to selfs context.
        :type other_context: list[str | JSON_LD_CONTEXT_DICT] | None

        :return:
        :rtype: None
        """
        if other_context:
            if not isinstance(self.context, list):
                self.context = [self.context]
            if isinstance(other_context, list):
                self.context = [*other_context, *self.context]
            else:
                self.context = [other_context, *self.context]

            # update the active context that is used for compaction/ expansion
            self.active_ctx = self.ld_proc.initial_ctx(self.context, {"documentLoader": bundled_loader})

    def update(self: Self, other: ld_dict) -> None:
        """
        Updates/ Merges this ld_merge dict with the given ld_dict other.
        This overwrites :meth:`ld_dict.update`, and may cause unexpected behavior if not used carefully.

        :param self: The ld_merge_dict that is updated with other.
        :type self: Self
        :param other: The ld_container that is merged into self.
        :type other: ld_dict

        :return:
        :rtype: None
        """
        # update add all new context
        if isinstance(other, ld_dict):
            self.update_context(other.context)

        # add the acutal values based on the MergeAction strategies
        # this works implicitly because ld_dict.update invokes self.__setitem__ which is overwritten by ld_merge_dict
        super().update(other)

    def add_strategy(self: Self, strategy: dict[Union[str, None], dict[Union[str, None], MergeAction]]) -> None:
        """
        Adds the given strategy to the self.strategies.

        :param self: The ld_merge_dict the strategy is added to.
        :type self: Self
        :param strategy: The object describing how which object types are supposed to be merged.
        :type strategy: dict[str | None, dict[str | None, MergeAction]]
        """
        for key, value in strategy.items():
            self.strategies[key] = {**value, **self.strategies.get(key, {})}

    def __setitem__(self: Self, key: str, value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]):
        """
        Creates the new entry for self[key] using self.strategies on the values in self[key] and value.
        Wraps :meth:`ld_dict.__setitem__`, and may cause unexpected behavior if not used carefully.

        :param self: The ld_merge_dict whose value at key gets updated/ merged with value.
        :type self: Self
        :param key: The key at whicht the value is updated/ merged at in self.
        :type key: str
        :param value: The value that is merged into self[key].
        :type value: JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list
        """
        # create the new item if self[key] and value have to be merged.
        if key in self:
            value = self._merge_item(key, value)
        # update the entry of self[key]
        super().__setitem__(key, value)

    def match(
        self: Self,
        key: str,
        value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list],
        match: Callable[[Any, Any],  bool]
    ) -> Union[BASIC_TYPE, TIME_TYPE, "ld_merge_dict", ld_merge_list]:
        """
        Returns the first item in self[key] for which match(item, value) returns true.
        If no such item is found None is returned instead.

        :param self: The ld_merge_dict in whose entry for key a match for value is searched.
        :type self: Self
        :param key: The key to the items in self in which a match for value is searched.
        :type key: str
        :param value: The value a match is searched for in self[key].
        :type value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
        :param match: The method defining if two objects are a match.
        :type match: Callable[[Any, Any], bool]

        :return: The item in self[key] that is a match to value if one exists else None
        :rtype: BASIC_TYPE | TIME_TYPE | ld_merge_dict | ld_merge_list
        """
        # iterate over all items in self[key] and return the first that is a match
        for item in self[key]:
            if match(item, value):
                return item

    def _merge_item(
        self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[BASIC_TYPE, TIME_TYPE, "ld_merge_dict", ld_merge_list]:
        """
        Applies the most suitable merge strategy to merge self[key] and value and then returns the result.

        :param self: The ld_merge_dict whose entry at key is to be merged with value.
        :type self: Self
        :param key: The key to the entry in self that is to be merged with value.
        :type key: str
        :param value: The value that is to be merged with self[key].
        :type value: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return: The result of the merge from self[key] with value.
        :rtype: BASIC_TYPE | TIME_TYPE | ld_merge_dict | ld_merge_list
        """
        # search for all applicable strategies
        strategy = {**self.strategies[None]}
        ld_types = self.data_dict.get('@type', [])
        for ld_type in ld_types:
            strategy.update(self.strategies.get(ld_type, {}))

        # choose one merge strategy and return the item returned by following the merge startegy
        merger = strategy.get(key, strategy[None])
        return merger.merge(self, [*self.path, key], self[key], value)

    def _add_related(
        self: Self, rel: str, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> None:
        """
        Adds an entry for rel to self containing which key and value is affected.

        :param self: The ld_merge_container the special entry is added to.
        :type self: Self
        :param rel: The "type" of the special entry (used as the key).
        :type rel: str
        :param key: The key of the affected key, value pair in self.
        :type key: str
        :param value: The value of the affected key, value pair in self.
        :type value:  BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return:
        :rtype: None
        """
        # FIXME: key not only string
        # make sure appending is possible
        self.emplace(rel)
        # append the new entry
        self[rel].append({"@type": "schema:PropertyValue", "schema:name": str(key), "schema:value": str(value)})

    def reject(self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Adds an entry to self containing containing information that the key, value pair
        key, value has been rejected in the merge.
        For further information see :meth:`ld_merge_dict._add_related`.

        :param self: The ld_merge_container the special entry is added to.
        :type self: Self
        :param key: The key of the rejected key, value pair in self.
        :type key: str
        :param value: The value of the rejected key, value pair in self.
        :type value: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return:
        :rtype: None
        """
        # FIXME: key not only string
        self._add_related("hermes-rt:reject", key, value)

    def replace(self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Adds an entry to self containing containing information that the key, value pair
        key, value was replaced in the merge.
        For further information see :meth:`ld_merge_dict._add_related`.

        :param self: The ld_merge_container the special entry is added to.
        :type self: Self
        :param key: The key of the old key, value pair in self.
        :type key: str
        :param value: The value of the old key, value pair in self.
        :type value: BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return:
        :rtype: None
        """
        # FIXME: key not only string
        self._add_related("hermes-rt:replace", key, value)
