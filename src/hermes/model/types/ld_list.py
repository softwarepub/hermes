# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from types import NotImplementedType
from .ld_container import (
    ld_container,
    JSON_LD_CONTEXT_DICT,
    EXPANDED_JSON_LD_VALUE,
    COMPACTED_JSON_LD_VALUE,
    JSON_LD_VALUE,
    TIME_TYPE,
    BASIC_TYPE,
)

from typing import Generator, Union, Self


class ld_list(ld_container):
    """ An JSON-LD container resembling a list ("@set", "@list" or "@graph"). """

    def __init__(
        self: Self,
        data: Union[list[str], list[dict[str, Union[BASIC_TYPE, EXPANDED_JSON_LD_VALUE]]]],
        *,
        parent: Union["ld_container", None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
    ) -> None:
        """
        Create a new ld_list.py container.

        :param self: The instance of ld_list to be initialized.
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
        # check for validity of data
        if not isinstance(key, str):
            raise ValueError("The key is not a string or was omitted.")
        if not isinstance(data, list):
            raise ValueError("The given data does not represent an ld_list.")
        # infer the container type and item_list from data
        if self.is_ld_list(data):
            if "@list" in data[0]:
                self.container_type = "@list"
                self.item_list: list = data[0]["@list"]
            elif "@graph" in data[0]:
                self.container_type = "@graph"
                self.item_list: list = data[0]["@graph"]
            else:
                raise ValueError("The given @set is not fully expanded.")
        else:
            self.container_type = "@set"
            self.item_list: list = data
        # further validity checks
        if key == "@type":
            if any(not isinstance(item, str) for item in self.item_list) or self.container_type != "@set":
                raise ValueError("A given value for @type is not a string.")
        elif any(not isinstance(item, dict) for item in self.item_list):
            raise ValueError("A given value is not properly expanded.")
        # call super constructor
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    def __getitem__(
        self: Self, index: Union[int, slice]
    ) -> Union[BASIC_TYPE, TIME_TYPE, ld_container, list[Union[BASIC_TYPE, TIME_TYPE, ld_container]]]:
        """
        Get the item(s) at position index in a pythonized form.

        :param self: The ld_list the items are taken from.
        :type self: Self
        :param index: The positon(s) from which the item(s) is/ are taken.
        :type index: int | slice

        :return: The pythonized item(s) at index.
        :rtype: BASIC_TYPE | TIME_TYPE | ld_container | list[BASIC_TYPE | TIME_TYPE | ld_container]]
        """
        # handle slices by applying them to a list of indices and then getting the items at those
        if isinstance(index, slice):
            return [self[i] for i in [*range(len(self))][index]]

        # get the item from the item_list and pythonize it. If necessary add the index.
        item = self._to_python(self.key, self.item_list[index])
        if isinstance(item, ld_container):
            item.index = index
        return item

    def __setitem__(
        self: Self, index: Union[int, slice], value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]
    ) -> None:
        """
        Set the item(s) at position index to the given value(s).
        All given values are expanded. If any are assimilated by self all items that would be added by this are added.

        :param self: The ld_list the items are set in.
        :type self: Self
        :param index: The positon(s) at which the item(s) is/ are set.
        :type index: int | slice
        :param value: The new value(s).
        :type value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]

        :return:
        :rtype: None
        """
        if not isinstance(index, slice):
            # expand the value
            value = self._to_expanded_json([value])
            # the returned value is always a list but my contain more then one item
            # therefor a slice on the item_list is used to add the expanded value(s)
            if index != -1:
                self.item_list[index:index+1] = value
            else:
                self.item_list[index:] = value
            return
        # check if the given values can be iterated (value does not have to be a list)
        try:
            iter(value)
        except TypeError as exc:
            raise TypeError("must assign iterable to extended slice") from exc
        # expand the values and merge all expanded values into one list
        expanded_value = ld_container.merge_to_list(*[self._to_expanded_json([val]) for val in value])
        # set the values at index to the expanded values
        self.item_list[index] = [val[0] if isinstance(val, list) else val for val in expanded_value]

    def __delitem__(self: Self, index: Union[int, slice]) -> None:
        """
        Delete the item(s) at position index.
        Note that if a deleted object is represented by an ld_container druing this process it will still exist
        and not be modified afterwards.

        :param self: The ld_list the items are deleted from.
        :type self: Self
        :param index: The positon(s) at which the item(s) is/ are deleted.
        :type index: int | slice

        :return:
        :rtype: None
        """
        del self.item_list[index]

    def __len__(self: Self) -> int:
        """
        Returns the number of items in this ld_list.

        :param self: The ld_list whose length is to be returned.
        :type self: Self

        :return: The length of self.
        :rtype: int
        """
        return len(self.item_list)

    def __iter__(self: Self) -> Generator[Union[BASIC_TYPE | TIME_TYPE | ld_container], None, None]:
        """
        Returns an iterator over the pythonized values contained in self.

        :param self: The ld_list over whose items is iterated.
        :type self: Self

        :return: The Iterator over self's values.
        :rtype: Generator[Union[BASIC_TYPE | TIME_TYPE | ld_container], None, None]
        """
        # return an Iterator over each value in self in its pythonized from
        for index, value in enumerate(self.item_list):
            item = self._to_python(self.key, value)
            # add which entry an ld_container is stored at, if item is an ld_container
            if isinstance(item, ld_container):
                item.index = index
            yield item

    def __contains__(self: Self, value: JSON_LD_VALUE) -> bool:
        """
        Returns whether or not value is contained in self.
        Note that it is not directly checked if value is in self.item_list.
        First value is expanded then it is checked if value is in self.item_list.
        If however value is assimilated by self it is checked if all values are contained in self.item_list.
        Also note that the checks whether the expanded value is in self.item_list is based on ld_list.__eq__.
        That means that this value is 'contained' in self.item_list if any object in self.item_list
        has the same @id like it or it xor the object in the item_list has an id an all other values are the same.

        :param self: The ld_list that is checked if it contains value.
        :type self: Self
        :param value: The object being checked whether or not it is in self.
        :type value: JSON_LD_VALUE

        :return: Whether or not value is being considered to be contained in self.
        :rtype: bool
        """
        # expand value
        expanded_value = self._to_expanded_json([value])
        # empty list -> no value to check
        if len(expanded_value) == 0:
            return True
        # call contains on all items in the expanded list if it contains more then one item
        # and return true only if all calls return true
        if len(expanded_value) > 1:
            return all(val in self for val in expanded_value)
        self_attributes = {"parent": self.parent, "key": self.key, "index": self.index, "context": self.full_context}
        # create a temporary list containing the expanded value
        # check for equality with a list containg exactly one item from self.item_list for every item in self.item_list
        # return true if for any item in self.item_list this check returns true
        if self.container_type == "@set":
            temp_list = ld_list(expanded_value, **self_attributes)
            return any(temp_list == ld_list([val], **self_attributes) for val in self.item_list)
        temp_list = ld_list([{self.container_type: expanded_value}], **self_attributes)
        return any(temp_list == ld_list([{self.container_type: [val]}], **self_attributes) for val in self.item_list)

    def __eq__(
        self: Self,
        other: Union[
            "ld_list",
            list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]],
            dict[str, list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]],
        ],
    ) -> Union[bool, NotImplementedType]:
        """
        Returns wheter or not self is considered to be equal to other.
        If other is not an ld_list, it is converted first.
        For each index it is checked if the ids of the items at index in self and other match if both have one,
        if only one has an id all other values are compared.
        If self or other is considered unordered the comparison is more difficult and ...

        :param self: The ld_list other is compared to.
        :type self: Self
        :param other: The list/ container/ ld_list self is compared to.
        :type other: ld_list | list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]
            | dict[str, list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]]

        :return: Whether or not self and other are considered equal.
            If other is of the wrong type return NotImplemented instead.
        :rtype: bool | NotImplementedType
        """
        # TODO: ld_lists with container_type "@set" have to be considered unordered
        # check if other has an acceptable type
        if not (isinstance(other, (list, ld_list)) or ld_list.is_container(other)):
            return NotImplemented

        # convert other into an ld_list if it isn't one already
        if isinstance(other, dict):
            other = [other]
        if isinstance(other, list):
            if ld_list.is_ld_list(other):
                other = ld_list.get_item_list_from_container(other[0])
            other = self.from_list(other, parent=self.parent, key=self.key, context=self.context)

        # check if the length matches
        if len(self.item_list) != len(other.item_list):
            return False

        # check for special case (= key is @type)
        if (self.key == "@type") ^ (other.key == "@type"):
            return False
        if self.key == other.key == "@type":
            # lists will only contain string
            return self.item_list == other.item_list

        # check if at each index the items are considered equal
        for index, (item, other_item) in enumerate(zip(self.item_list, other.item_list)):
            # check if items are values
            if ((ld_container.is_typed_json_value(item) or ld_container.is_json_value(item)) and
                    (ld_container.is_typed_json_value(other_item) or ld_container.is_json_value(other_item))):
                if not ld_container.are_values_equal(item, other_item):
                    return False
                continue
            # check if both contain an id and compare 
            if "@id" in item and "@id" in other_item:
                if item["@id"] != other_item["@id"]:
                    return False
                continue
            # get the 'real' items (i.e. can also be ld_dicts or ld_lists)
            item = self[index]
            other_item = other[index]
            # compare using the correct equals method
            res = item.__eq__(other_item)
            if res == NotImplemented:
                # swap order if first try returned NotImplemented
                res = other_item.__eq__(item)
            # return false if the second comparison also fails or one of them returned false
            if res is False or res == NotImplemented:
                return False

        # return true because no unequal elements where found
        return True

    def __ne__(
        self: Self,
        other: Union[
            "ld_list",
            list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]],
            dict[str, list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]],
        ],
    ) -> Union[bool, NotImplementedType]:
        """
        Returns whether or not self and other not considered to be equal.
        (Returns not self.__eq__(other) if the return type is bool.
        See ld_list.__eq__ for more details on the comparison.)

        :param self: The ld_list other is compared to.
        :type self: Self
        :param other: The list/ container/ ld_list self is compared to.
        :type other: ld_list | list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]
            | dict[str, list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]]

        :return: Whether or not self and other are not considered equal.
            If other is of the wrong type return NotImplemented instead.
        :rtype: bool | NotImplementedType
        """
        # compare self and other using __eq__
        x = self.__eq__(other)
        # return NotImplemented if __eq__ did so and else the inverted result of __eq__
        if x is NotImplemented:
            return NotImplemented
        return not x

    def append(self, value):
        self.item_list.extend(self._to_expanded_json([value]))

    def extend(self, value):
        for item in value:
            self.append(item)

    def to_python(self):
        return [
            item.to_python() if isinstance(item, ld_container) else item
            for item in self
        ]

    @classmethod
    def is_ld_list(cls, ld_value):
        return cls.is_ld_node(ld_value) and cls.is_container(ld_value[0])

    @classmethod
    def is_container(cls, value):
        return (
            isinstance(value, dict)
            and [*value.keys()] in [["@list"], ["@set"], ["@graph"]]
            and any(isinstance(value.get(cont, None), list) for cont in {"@list", "@set", "@graph"})
        )

    @classmethod
    def from_list(cls, value, *, parent=None, key=None, context=None, container_type="@set"):
        if key == "@type":
            container_type = "@set"
        if container_type != "@set":
            value = [{container_type: value}]
        if parent is not None:
            if isinstance(parent, ld_list):
                expanded_value = parent._to_expanded_json([value])
                if (len(expanded_value) != 1 or
                        not (isinstance(expanded_value[0], list) or cls.is_container(expanded_value[0]))):
                    parent.extend(expanded_value)
                    return parent
            else:
                expanded_value = parent._to_expanded_json({key: value})[cls.ld_proc.expand_iri(parent.active_ctx, key)]
        else:
            expanded_value = cls([], parent=None, key=key, context=context)._to_expanded_json(value)
        return cls(expanded_value, parent=parent, key=key, context=context)

    @classmethod
    def get_item_list_from_container(cls, ld_value):
        for cont in {"@list", "@set", "@graph"}:
            if cont in ld_value:
                return ld_value[cont]
        raise ValueError("The given data does not represent a container.")
