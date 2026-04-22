# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Union
from typing_extensions import Self

from hermes.model.types import ld_container, ld_context, ld_dict, ld_list
from hermes.model.types.ld_container import (
    BASIC_TYPE, EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT, JSON_LD_VALUE, TIME_TYPE
)
from hermes.model.types.pyld_util import bundled_loader
from .action import MergeError

if TYPE_CHECKING:
    from .action import MergeAction


class _ld_merge_container:
    """
    Abstract base class for ld_merge_dict and ld_merge_list,
    providing the merge containers with an override of :meth:`ld_container._to_python`.
    See also :class:`ld_dict`, :class:`ld_list` and :class:`ld_container`.
    """

    def _to_python(
        self: Self,
        full_iri: str,
        ld_value: Union[EXPANDED_JSON_LD_VALUE, dict[str, EXPANDED_JSON_LD_VALUE], list[str], str]
    ) -> Union["ld_merge_dict", "ld_merge_list", BASIC_TYPE, TIME_TYPE]:
        """
        Returns a pythonized version of ``ld_value`` pretending the value is in ``self`` and ``full_iri`` its key.

        Args:
            full_iri (str): The expanded iri of the key of ``ld_value`` / ``self`` (later if self is not a dictionary).
            ld_value (EXPANDED_JSON_LD_VALUE | dict[str, EXPANDED_JSON_LD_VALUE] | list[str] | str):
                The value thats pythonized value is requested. ``ld_value`` has to be valid expanded JSON-LD if it
                was embeded in ``self._data``.

        Returns:
            ld_merge_dict | ld_merge_list | BASIC_TYPE | TIME_TYPE: The pythonized value of ``ld_value``.
        """
        value = super()._to_python(full_iri, ld_value)
        # replace ld_dicts with ld_merge_dicts
        if isinstance(value, ld_dict) and not isinstance(value, ld_merge_dict):
            value = ld_merge_dict(
                value.ld_value,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context,
                strategies=self.strategies
            )
        # replace ld_lists with ld_merge_lists
        if isinstance(value, ld_list) and not isinstance(value, ld_merge_list):
            value = ld_merge_list(
                value.ld_value,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context,
                strategies=self.strategies
            )
        return value


class ld_merge_list(_ld_merge_container, ld_list):
    """
    ld_list wrapper to ensure the 'merge_container'-property does not get lost, while merging.
    See also :class:`ld_list` and :class:`ld_merge_container`.

    Attributes:
        strategies (dict[str | None, dict[str | None, MergeAction]]): The strategies used inside the child
            ld_merge_dicts.
    """

    def __init__(
        self: "ld_merge_list",
        data: Union[list[str], list[dict[str, EXPANDED_JSON_LD_VALUE]]],
        *,
        parent: Union[ld_container, None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
        strategies: dict[Union[str, None], dict[Union[str, None], MergeAction]] = {}
    ) -> None:
        """
        Create a new ld_merge_list.
        For further information on this function and the errors it throws see :meth:`ld_list.__init__`.

        Args:
            data (list[str] | list[dict[str, BASIC_TYPE | EXPANDED_JSON_LD_VALUE]]):
                The expanded json-ld data that is
            parent (ld_container | None): parent node of this container.
            key (str | None): key into the parent container.
            index (int | None): index into the parent container.
            context (list[str | JSON_LD_CONTEXT_DICT] | None): local context for this container.
            strategies (dict[str | None, dict[str | None, MergeAction]]): The strategies for merging in the childs.

        Returns:
            None:
        """
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        self.strategies = strategies


class ld_merge_dict(_ld_merge_container, ld_dict):
    """
    ld_dict wrapper providing methods to merge an object of this class with an ld_dict object.
    See also :class:`ld_dict` and :class:`ld_merge_container`.

    Attributes:
        strategies (dict[str | None, dict[str | None, MergeAction]]):
            The strategies for merging different types of values in the ld_dicts.
    """

    def __init__(
        self: Self,
        data: list[dict[str, EXPANDED_JSON_LD_VALUE]],
        *,
        parent: Union[ld_dict, ld_list, None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
        strategies: dict[Union[str, None], dict[Union[str, None], MergeAction]] = {}
    ) -> None:
        """
        Create a new instance of an ld_merge_dict. See also :meth:`ld_dict.__init__`.

        Args:
            data (EXPANDED_JSON_LD_VALUE): The expanded json-ld data that is mapped.
            parent (ld_dict | ld_list | None): parent node of this container.
            key (str | None): key into the parent container.
            index (int | None): index into the parent container.
            context (list[str | JSON_LD_CONTEXT_DICT] | None): local context for this container.
            strategies (dict[str | None, dict[str | None, MergeAction]]): The initial strategies.

        Returns:
            None:

        Raises:
            ValueError: If ``data`` doesn't represent an ld_dict.
        """
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        # add provernance context
        self.update_context(ld_context.HERMES_PROV_CONTEXT)

        # add strategies
        self.strategies = strategies

    def update_context(
        self: Self, other_context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None]
    ) -> None:
        """
        Updates ``self`` s context with ``other_context``.
        JSON-LD processing prioritizes the context values in order (first least important, last most important).

        Args:
            other_context (list[str | JSON_LD_CONTEXT_DICT] | None):
                The context object that is added to ``self`` s context.

        Returns:
            None:
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
        Updates/ Merges ``self`` with the given ld_dict ``other``.
        Note that this overwrites :meth:`ld_dict.update`, and may cause unexpected behavior if not used carefully.

        Args:
            other (ld_dict): The ld_container that is merged into ``self``.

        Returns:
            None:
        """
        # update add all new context
        if isinstance(other, ld_dict):
            self.update_context(other.context)

        # add the acutal values based on the MergeAction strategies
        # this works implicitly because ld_dict.update invokes self.__setitem__ which is overwritten by ld_merge_dict
        super().update(other)

    def add_strategy(self: Self, strategy: dict[Union[str, None], dict[Union[str, None], MergeAction]]) -> None:
        """
        Adds ``strategy`` to the ``self.strategies``.

        Args:
            strategy (dict[str | None, dict[str | None, MergeAction]]): The object describing how which object types are
                supposed to be merged.

        Returns:
            None:
        """
        for key, value in strategy.items():
            self.strategies[key] = {**value, **self.strategies.get(key, {})}

    def __setitem__(self: Self, key: str, value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Creates the new entry for ``self[key]`` using ``self.strategies`` on the values in ``self[key]`` and ``value``.
        Note that this overwrites :meth:`ld_dict.__setitem__` and may cause unexpected behavior if not used carefully.

        Args:
            key (str): The key at which the value is updated/ merged at in ``self``.
            value (JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is merged into
                ``self[key]``.
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
        Returns the first item in ``self[key]`` for which ``match(item, value)`` returns ``True``.
        If no such item is found ``None`` is returned instead.

        Args:
            key (str): The key to the items in ``self`` from which a match for ``value`` is searched.
            value (Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]): The value a match is searched for in
                ``self[key]``.
            match (Callable[[Any, Any], bool]): The method defining if two objects are a match.

        Returns:
            BASIC_TYPE | TIME_TYPE | ld_merge_dict | ld_merge_list:
                The item in ``self[key]`` that is a match for``value`` if one exists otherwise ``None``.
        """
        # iterate over all items in self[key] and return the first that is a match
        for item in self[key]:
            if match(item, value):
                return item

    def _merge_item(
        self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> Union[BASIC_TYPE, TIME_TYPE, "ld_merge_dict", ld_merge_list]:
        """
        Applies the most suitable merge strategy to merge ``self[key]`` and value and then returns the result.

        Args:
            key (str): The key to the entry in ``self`` that is to be merged with ``value``.
            value (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is to be merged with ``self[key]``.

        Returns:
            BASIC_TYPE | TIME_TYPE | ld_merge_dict | ld_merge_list:
                The result of the merge from ``self[key]`` with ``value``.

        Raises:
            MergeError: If there is no strategy for this key.
        """
        # search for all applicable strategies
        strategy = {**self.strategies.get(None, {})}
        ld_types = self.data_dict.get('@type', [])
        for ld_type in ld_types:
            strategy.update(self.strategies.get(ld_type, {}))

        # choose one merge strategy and return the item returned by following the merge startegy
        merger = strategy.get(key, strategy.get(None, None))
        if merger is None:
            raise MergeError(f"Can't merge, no strategy found for key '{key}'.")
        return merger.merge(self, [*self.path, key], self[key], value)

    def _add_related(
        self: Self, rel: str, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> None:
        """
        Adds an entry for ``rel`` to ``self`` containing which key and value is affected.

        Args:
            rel (str): The "type" of the special entry (used as the key).
            key (str): The key of the affected key, value pair in ``self``.
            value (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value of the affected key, value pair in ``self``.

        Returns:
            None:
        """
        # FIXME: key not only string
        # make sure appending is possible
        self.emplace(rel)
        # append the new entry
        self[rel].append({"@type": "schema:PropertyValue", "schema:name": str(key), "schema:value": str(value)})

    def reject(self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Adds an entry to ``self`` containing containing information that the key, value pair
        ``key``, ``value`` has been rejected in the merge.
        For further information see :meth:`ld_merge_dict._add_related`.

        Args:
            key (str): The key of the rejected key, value pair in ``self``.
            value (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value of the rejected key, value pair in ``self``.

        Returns:
            None:
        """
        # FIXME: key not only string
        self._add_related("hermes-rt:reject", key, value)

    def replace(self: Self, key: str, value: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Adds an entry to ``self`` containing containing information that the key, value pair
        ``key``, ``value`` was replaced in the merge.
        For further information see :meth:`ld_merge_dict._add_related`.

        Args:
            key (str): The key of the old key, value pair in ``self``.
            value (BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value of the old key, value pair in ``self``.

        Returns:
            None:
        """
        # FIXME: key not only string
        self._add_related("hermes-rt:replace", key, value)
