# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from collections.abc import Generator, Iterator, KeysView
from typing import Any, Literal, Optional, Union, TYPE_CHECKING
from typing_extensions import Self

from .ld_container import (
    ld_container,
    JSON_LD_CONTEXT_DICT,
    EXPANDED_JSON_LD_VALUE,
    NATIVE_LD_CONTAINER,
    JSON_LD_VALUE,
    TIME_TYPE,
    BASIC_TYPE,
)
from .pyld_util import bundled_loader
if TYPE_CHECKING:
    from .ld_list import ld_list


class ld_dict(ld_container):
    """
    An JSON-LD container resembling a dict.
    See also :class:`ld_container`

    Attributes:
        data_dict (dict[str, EXPANDED_JSON_LD_VALUE]): The dict of items (in expanded JSON-LD form)
            that are contained in this ld_dict.
        _NO_DEFAULT (type[str]): (class attribute) A type used as a placeholder to represent "no default".
    """
    _NO_DEFAULT = type("NO DEFAULT")

    def __init__(
        self: Self,
        data: list[dict[str, EXPANDED_JSON_LD_VALUE]],
        *,
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = None,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = None
    ) -> None:
        """
        Create a new instance of an ld_dict.

        Args:
            data (EXPANDED_JSON_LD_VALUE): The expanded json-ld data that is mapped.
            parent (ld_dict | ld_list | None): parent node of this container.
            key (str | None): key into the parent container.
            index (int | None): index into the parent container.
            context (list[str | JSON_LD_CONTEXT_DICT] | None): local context for this container.

        Returns:
            None:

        Raises:
            ValueError: If the given data doesn't represent an ld_dict.
        """
        # check for validity of data
        if not self.is_ld_dict(data):
            raise ValueError("The given data does not represent a ld_dict.")
        self.data_dict = data[0]
        # call super constructor
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    def __getitem__(self: Self, key: str) -> ld_list:
        """
        Get the item with the given key in as a ld_list.\n
        If self contains no key, value pair with the given key, then an empty list is added as its value and returned.

        Args:
            key (str): The key (compacted or expanded) to the item.

        Returns:
            ld_list: The ld_list item at the key.
        """
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        return self._to_native_python(full_iri, self.data_dict[full_iri])

    def __setitem__(self: Self, key: str, value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Set the item at the given key to the given value or delete it if value is None.
        The given value is expanded.

        Args:
            key (str): The key at which the item is set.
            value (JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The new value.

        Returns:
            None:
        """
        # if the value is None delete the entry instead of updating it, but make sure it exists before deleting
        if value is None and key not in self:
            return
        if value is None:
            del self[self.ld_proc.expand_iri(self.active_ctx, key)]
            return
        # expand the key, value pair and update data_dict
        ld_value = self._to_expanded_json({key: value})
        self.data_dict.update(ld_value)

    def __delitem__(self: Self, key: str) -> None:
        """
        Delete the key, value pair with the given value pair.\n
        Note that if a deleted object is represented by an ld_container druing this process it will still exist
        and not be modified afterwards.

        Args:
            key (str): The key (expanded or compacted) of the key, value pair that is deleted.

        Returns:
            None:
        """
        # expand key and delete the key, value pair
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        del self.data_dict[full_iri]

    def __contains__(self: Self, key: str) -> bool:
        """
        Returns whether or not self contains a key, value pair with the given key.

        Args:
            key (str): The key for which it is checked if a key, value pair is contained in self.

        Returns:
            bool: Whether or not self contains a key, value pair with the given key.
        """
        # expand the key and check if self contains a key, value pair with it
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        return full_iri in self.data_dict

    def __eq__(
        self: Self, other: Union[ld_dict, dict[str, Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]]]
    ) -> bool:
        """
        Returns wheter or not self is considered to be equal to other.\n
        If other is not an ld_dict, it is converted first.\n
        If an id check is possible return its result otherwise:\n
        For each key, value pair its value is compared to the value with the same key in other.

        Note that due to those circumstances equality is not transitve
        meaning if a == b and b == c it is not guaranteed that a == c.

        Args:
            other (ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]):
                The dict/ ld_dict self is compared to.

        Returns:
            bool: Whether or not self and other are considered equal.
                If other is of the wrong type return the NotImplemented singleton instead.
        """
        # check if other has an acceptable type
        if not isinstance(other, (dict, ld_dict)):
            return NotImplemented

        # compare in the special case that other is a json_id or json_value
        if ld_container.is_json_id(other):
            if "@id" in self:
                return self["@id"] == other["@id"]
            return self.data_dict == {}
        if ld_container.is_json_value(other):
            if {*self.keys()}.issubset({"@id", *other.keys()}):
                return ld_container.are_values_equal(self.data_dict, other)
            return False

        # convert into an ld_dict if other is not one
        if isinstance(other, dict):
            other = self.from_dict(other, parent=self.parent, key=self.key, context=self.context)

        # check for id equality
        if "@id" in self and "@id" in other:
            return self["@id"] == other["@id"]

        # test for value equality
        keys_self = {*self.keys()}
        keys_other = {*other.keys()}
        unique_keys = keys_self.symmetric_difference(keys_other)
        if unique_keys and unique_keys != {"@id"}:
            # there is a key that isn't "@id" that is only in other or self
            return False
        # check if the values with the same key are equal
        for key in keys_self.intersection(keys_other):
            if self[key] != other[key]:
                return False
        return True

    def __ne__(
        self: Self, other: Union[ld_dict, dict[str, Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]]]
    ) -> bool:
        """
        Returns whether or not self and other not considered to be equal.\n
        (Returns not self.__eq__(other) if the return type is bool.
        See :meth:`ld_dict.__eq__` for more details on the comparison.)

        Args:
            other (ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]):
                The dict/ ld_dict self is compared to.

        Returns:
            bool:
                Whether or not self and other are not considered equal. If other is of the wrong type return the
                NotImplemented singleton instead.
        """
        # compare self and other using __eq__
        x = self.__eq__(other)
        # return NotImplemented if __eq__ did so and else the inverted result of __eq__
        if x is NotImplemented:
            return NotImplemented
        return not x

    def __bool__(self: Self) -> bool:
        """
        Returns the truth value self would have if it was a normal dict.\n
        I.e. returns true if no key, value pair is in self.

        Returns:
            bool: The truth value of self.
        """
        return bool(self.data_dict)

    def setdefault(
        self: Self,
        key: str,
        default: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_list:
        """
        Get the value for the given key if self has a value for the key. Otherwise set the value for key to default and
        then return the value at key in self.

        Args:
            key (str): The key at which the value is returned.
            default (JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list): The value that is set at key in self
                if there is no value for key in self.

        Returns:
            ld_list: The value at key in self (if no value at key in self, it is set to default first).
        """
        if key not in self:
            self[key] = default
        return self[key]

    def emplace(self: Self, key: str) -> None:
        """
        Emplace the value at key in self (it is set to an empty list) if there is no value yet.

        Args:
            key (str): The key at which the value in self is emplaced.

        Returns:
            None:
        """
        if key not in self:
            self[key] = []

    def get(
        self: Self, key: str, default: Any = _NO_DEFAULT
    ) -> Union[ld_list, Any]:
        """
        Get the item with the given key in as a ld_list using the build in get.\n
        If a KeyError is raised, return the default or reraise it if no default is given.

        Args:
            key (str): The key (compacted or expanded) to the item.

        Returns:
            ld_list: The ld_list item at the key.

        Raises:
            KeyError: If :meth:`__getitem__(key)` raised a KeyError and default isn't set.
        """
        try:
            return self[key]
        except KeyError as e:
            if default is self._NO_DEFAULT:
                raise e
            return default

    def update(
        self: Self,
        other: Union[ld_dict, dict[str, Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]]]
    ) -> None:
        """
        Set the items at the given keys to the given values or delete it if value is None by using build in set.

        Args:
            other (ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]):
                The key, value pairs giving the new values and their keys.

        Returns:
            None:
        """
        for key, value in other.items():
            self[key] = value

    def keys(self: Self) -> KeysView[str]:
        """
        Return the keys of the key, value pairs of self.

        Returns:
            KeysView[str]: The keys of the values in self.
        """
        return self.data_dict.keys()

    def compact_keys(self: Self) -> Iterator[str]:
        """
        Return an iterator of the compacted keys of the key, value pairs of self.

        Returns:
            Iterator[str]: An iterator over the compacted keys in self.
        """
        return map(
            lambda k: self.ld_proc.compact_iri(self.active_ctx, k),
            self.data_dict.keys()
        )

    def items(self: Self) -> Generator[tuple[str, ld_list], None, None]:
        """
        Return an generator of tuples of keys and their values in self.

        Returns:
            Generator[tuple[str, ld_list], None, None]: A Generator over all key, value pairs in self.
        """
        for k in self.data_dict.keys():
            yield k, self[k]

    @property
    def ref(self: Self) -> dict[Literal["@id"], str]:
        """
        Return the dict used to reference this object by its id. (Its form is {"@id": ...})

        Returns:
            dict[Literal["@id"], str]: The minimal JSON_LD object referencing self.

        Raises:
            KeyError: If self has no value for "@id".
        """
        return {"@id": self.data_dict['@id']}

    def to_native_python(self: Self) -> dict[str, Union[BASIC_TYPE, TIME_TYPE, NATIVE_LD_CONTAINER]]:
        """
        Return a native python version of this object where all ld_container are replaced by lists and dicts.

        Returns:
            dict[str, BASIC_TYPE | TIME_TYPE | NATIVE_LD_CONTAINER]: The native python version of self.
        """
        res = {}
        for key in self.compact_keys():
            value = self[key]
            if isinstance(value, ld_container):
                value = value.to_native_python()
            res[key] = value
        return res

    # FIXME: Allow from_dict to handle dicts containing ld_dicts and ld_lists
    @classmethod
    def from_dict(
        cls: type[Self],
        value: dict[str, NATIVE_LD_CONTAINER],
        *,
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = None,
        context: Optional[Union[str, JSON_LD_CONTEXT_DICT, list[Union[str, JSON_LD_CONTEXT_DICT]]]] = None,
        ld_type: Optional[Union[str, list[str]]] = None
    ) -> ld_dict:
        """
        Creates a ld_dict from the given dict with the given parent, key, context and ld_type.\n
        Uses the expansion of the JSON-LD Processor and not the one of ld_container.

        Args:
            value (dict[str, NATIVE_LD_CONTAINER]): The dict of values the ld_dict should be created from.
            parent (ld_dict | ld_list | None): The parent container of the new ld_list.
            key (str | None): The key into the inner most parent container representing a dict of the new ld_list.
            context (str | JSON_LD_CONTEXT_DICT | list[str | JSON_LD_CONTEXT_DICT] | None):
                The context for the new dict (it will also inherit the context of parent).
            ld_type (str | list[str] | None): Additional value(s) for the new dict.

        Returns:
            ld_dict: The new ld_dict build from value.
        """
        # make a copy of value and add the new type to it.
        ld_data = value.copy()
        ld_type = ld_container.merge_to_list(ld_type or [], ld_data.get('@type', []))
        if ld_type:
            ld_data["@type"] = ld_type

        # generate the context from value, context and parent
        data_context = ld_data.pop('@context', [])
        merged_contexts = ld_container.merge_to_list(data_context, context or [])
        full_context = []
        if parent is None and merged_contexts:
            ld_data["@context"] = merged_contexts
        elif parent is not None:
            full_context = parent.full_context + merged_contexts

        # expand value and create an ld_dict from it
        ld_value = cls.ld_proc.expand(ld_data, {"expandContext": full_context, "documentLoader": bundled_loader})
        ld_value = ld_dict(ld_value, parent=parent, key=key, context=merged_contexts)

        return ld_value

    @classmethod
    def is_ld_dict(cls: type[Self], ld_value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an expanded json-ld dict.\n
        I.e. if ld_value is a list containing a dict containing none of the keys "@set", "@graph", "@list" and "@value"
        and not only the key "@id".

        Args:
            ld_value (Any): The value that is checked.

        Returns:
            bool: Wheter or not ld_value could represent an expanded json-ld dict.
        """
        return cls.is_ld_node(ld_value) and cls.is_json_dict(ld_value[0])

    @classmethod
    def is_json_dict(cls: type[Self], ld_value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an expanded json-ld dict.\n
        I.e. if ld_value is a dict containing none of the keys "@set", "@graph", "@list" and "@value"
        and not only the key "@id".

        Args:
            ld_value (Any): The value that is checked.

        Returns:
            bool: Wheter or not ld_value could represent an expanded json-ld dict.
        """
        if not isinstance(ld_value, dict):
            return False

        if any(k in ld_value for k in ["@set", "@graph", "@list", "@value"]):
            return False

        return True
