# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from .pyld_util import bundled_loader
from .ld_container import ld_container

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Generator, Iterator, KeysView
    from .ld_container import (
        JSON_LD_CONTEXT_DICT,
        EXPANDED_JSON_LD_VALUE,
        PYTHONIZED_LD_CONTAINER,
        JSON_LD_VALUE,
        TIME_TYPE,
        BASIC_TYPE,
    )
    from .ld_list import ld_list
    from typing import Any, Union, Literal
    from typing_extensions import Self


class ld_dict(ld_container):
    """
    An JSON-LD container resembling a dict.
    See also :class:`ld_container`

    :ivar ref: A dict used to reference this object by its id. (Its form is {"@id": ...})
    :ivartype ref: dict[Literal["@id"], str]

    :cvar container_type: A type used as a placeholder to represent "no default".
    :cvartype container_type: type[str]
    """
    _NO_DEFAULT = type("NO DEFAULT")

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
        Create a new instance of an ld_dict.

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
        # check for validity of data
        if not self.is_ld_dict(data):
            raise ValueError("The given data does not represent a ld_dict.")
        self.data_dict = data[0]
        # call super constructor
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    def __getitem__(self: Self, key: str) -> ld_list:
        """
        Get the item with the given key in a pythonized form.
        If self contains no key, value pair with the given key, then an empty list is added as its value and returned.

        :param self: The ld_dict the item is taken from.
        :type self: ld_dict
        :param key: The key (compacted or expanded) to the item.
        :type key: str

        :return: The pythonized item at the key.
        :rtype: ld_list
        """
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        if full_iri not in self.data_dict:
            self[full_iri] = []
        ld_value = self.data_dict[full_iri]
        return self._to_python(full_iri, ld_value)

    def __setitem__(self: Self, key: str, value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]) -> None:
        """
        Set the item at the given key to the given value or delete it if value is None.
        The given value is expanded.

        :param self: The ld_dict the item is set in.
        :type self: ld_dict
        :param key: The key at which the item is set.
        :type key: str
        :param value: The new value.
        :type value: JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list

        :return:
        :rtype: None
        """
        # if the value is None delete the entry instead of updating it
        if value is None:
            del self[self.ld_proc.expand_iri(self.active_ctx, key)]
            return
        # expand the key, value pair and update data_dict
        ld_value = self._to_expanded_json({key: value})
        self.data_dict.update(ld_value)

    def __delitem__(self: Self, key: str) -> None:
        """
        Delete the key, value pair with the given value pair.
        Note that if a deleted object is represented by an ld_container druing this process it will still exist
        and not be modified afterwards.

        :param self: The ld_dict the key, value pair is deleted from.
        :type self: ld_dict
        :param key: The key (expanded or compacted) of the key, value pair that is deleted.
        :type key: str

        :return:
        :rtype: None
        """
        # expand key and delete the key, value pair
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        del self.data_dict[full_iri]

    def __contains__(self: Self, key: str) -> bool:
        """
        Returns whether or not self contains a key, value pair with the given key.

        :param self: The ld_dict that is checked if it a key, value pair with the given key.
        :type self: ld_dict
        :param key: The key for which it is checked if a key, value pair is contained in self.
        :type key: str

        :return: Whether or not self contains a key, value pair with the given key.
        :rtype: bool
        """
        # expand the key and check if self contains a key, value pair with it
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        # FIXME: is that good?
        return full_iri in self.data_dict

    def __eq__(
        self: Self, other: Union[ld_dict, dict[str, Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]]]
    ) -> bool:
        """
        Returns wheter or not self is considered to be equal to other.<br>
        If other is not an ld_dict, it is converted first.
        If an id check is possible return its result otherwise:
        For each key, value pair its value is compared to the value with the same key in other.
        Note that due to those circumstances equality is not transitve
        meaning if a == b and b == c it is not guaranteed that a == c.<br>

        :param self: The ld_dict other is compared to.
        :type self: ld_dict
        :param other: The dict/ ld_dict self is compared to.
        :type other: ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]

        :return: Whether or not self and other are considered equal.
            If other is of the wrong type return the NotImplemented singleton instead.
        :rtype: bool
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
        Returns whether or not self and other not considered to be equal.
        (Returns not self.__eq__(other) if the return type is bool.
        See ld_list.__eq__ for more details on the comparison.)

        :param self: The ld_dict other is compared to.
        :type self: ld_dict
        :param other: The dict/ ld_dict self is compared to.
        :type other: ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]

        :return: Whether or not self and other are not considered equal.
            If other is of the wrong type return the NotImplemented singleton instead.
        :rtype: bool
        """
        # compare self and other using __eq__
        x = self.__eq__(other)
        # return NotImplemented if __eq__ did so and else the inverted result of __eq__
        if x is NotImplemented:
            return NotImplemented
        return not x

    def get(
        self: Self, key: str, default: Any = _NO_DEFAULT
    ) -> Union[ld_list, Any]:
        """
        Get the item with the given key in a pythonized form using the build in get.
        If a KeyError is raised, return the default or reraise it if no default is given.

        :param self: The ld_dict the item is taken from.
        :type self: ld_dict
        :param key: The key (compacted or expanded) to the item.
        :type key: str

        :return: The pythonized item at the key.
        :rtype: ld_list

        :raises KeyError: If the build in get raised a KeyError.
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

        :param self: The ld_dict the items are set in.
        :type self: ld_dict
        :param other: The key, value pairs giving the new values and their keys.
        :type other: ld_dict | dict[str, JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_dict | ld_list]

        :return:
        :rtype: None
        """
        for key, value in other.items():
            self[key] = value

    def keys(self: Self) -> KeysView[str]:
        """
        Return the keys of the key, value pairs of self.

        :param self: The ld_dict whose keys are returned.
        :type self: ld_dict
        """
        return self.data_dict.keys()

    def compact_keys(self: Self) -> Iterator[str]:
        """
        Return an iterator of the compacted keys of the key, value pairs of self.

        :param self: The ld_dict whose compacted keys are returned.
        :type self: ld_dict
        """
        return map(
            lambda k: self.ld_proc.compact_iri(self.active_ctx, k),
            self.data_dict.keys()
        )

    def items(self: Self) -> Generator[tuple[str, ld_list], None, None]:
        """
        Return an generator of tuples of keys and their values in self.

        :param self: The ld_dict whose items are returned.
        :type self: ld_dict
        """
        for k in self.data_dict.keys():
            yield k, self[k]

    @property
    def ref(self: Self) -> dict[Literal["@id"], str]:
        """
        Return the dict used to reference this object by its id. (Its form is {"@id": ...})

        :param self: The ld_dict whose reference is returned.
        :type self: ld_dict

        :raises KeyError: If self has no id.
        """
        return {"@id": self.data_dict['@id']}

    def to_python(self: Self) -> dict[str, Union[BASIC_TYPE, TIME_TYPE, PYTHONIZED_LD_CONTAINER]]:
        """
        Return a fully pythonized version of this object where all ld_container are replaced by lists and dicts.

        :param self: The ld_dict whose fully pythonized version is returned.
        :type self: ld_dict

        :return: The fully pythonized version of self.
        :rtype: dict[str, BASIC_TYPE | TIME_TYPE | PYTHONIZED_LD_CONTAINER]
        """
        res = {}
        for key in self.compact_keys():
            value = self[key]
            if isinstance(value, ld_container):
                value = value.to_python()
            res[key] = value
        return res

    # FIXME: Allow from_dict to handle dicts containing ld_dicts and ld_lists
    @classmethod
    def from_dict(
        cls: type[Self],
        value: dict[str, PYTHONIZED_LD_CONTAINER],
        *,
        parent: Union[ld_dict, ld_list, None] = None,
        key: Union[str, None] = None,
        context: Union[str, JSON_LD_CONTEXT_DICT, list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
        ld_type: Union[str, list[str], None] = None
    ) -> ld_dict:
        """
        Creates a ld_dict from the given dict with the given parent, key, context and ld_type.<br>
        Uses the expansion of the JSON-LD Processor and not the one of ld_container.

        :param value: The dict of values the ld_dict should be created from.
        :type value: dict[str, PYTHONIZED_LD_CONTAINER]
        :param parent: The parent container of the new ld_list.
        :type parent: ld_dict | ld_list | None
        :param key: The key into the inner most parent container representing a dict of the new ld_list.
        :type: key: str | None
        :param context: The context for the new dict (it will also inherit the context of parent).
        :type context: str | JSON_LD_CONTEXT_DICT | list[str | JSON_LD_CONTEXT_DICT] | None
        :param ld_type: Additional value(s) for the new dict.
        :type ld_type: str | list[str] | None

        :return: The new ld_dict build from value.
        :rtype: ld_dict
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
        ld_value = cls(ld_value, parent=parent, key=key, context=merged_contexts)

        return ld_value

    @classmethod
    def is_ld_dict(cls: type[Self], ld_value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an expanded json-ld dict.<br>
        I.e. if ld_value is a list containing a dict containing none of the keys "@set", "@graph", "@list" and "@value"
        and not only the key "@id".

        :param ld_value: The value that is checked.
        :type ld_value: Any

        :returns: Wheter or not ld_value could represent an expanded json-ld dict.
        :rtype: bool
        """
        return cls.is_ld_node(ld_value) and cls.is_json_dict(ld_value[0])

    @classmethod
    def is_json_dict(cls: type[Self], ld_value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an expanded json-ld dict.<br>
        I.e. if ld_value is a dict containing none of the keys "@set", "@graph", "@list" and "@value"
        and not only the key "@id".

        :param ld_value: The value that is checked.
        :type ld_value: Any

        :returns: Wheter or not ld_value could represent an expanded json-ld dict.
        :rtype: bool
        """
        if not isinstance(ld_value, dict):
            return False

        if any(k in ld_value for k in ["@set", "@graph", "@list", "@value"]):
            return False

        if ['@id'] == [*ld_value.keys()]:
            return False

        return True
