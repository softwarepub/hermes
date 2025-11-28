# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from .ld_container import (
    ld_container,
    JSON_LD_CONTEXT_DICT,
    EXPANDED_JSON_LD_VALUE,
    COMPACTED_JSON_LD_VALUE,
    JSON_LD_VALUE,
    TIME_TYPE,
    BASIC_TYPE,
)

from typing import Union, Self, Any


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
                self.item_list = data[0]["@list"]
            elif "@graph" in data[0]:
                self.container_type = "@graph"
                self.item_list = data[0]["@graph"]
            else:
                raise ValueError("The given @set is not fully expanded.")
        else:
            self.container_type = "@set"
            self.item_list = data
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

    def __delitem__(self, index):
        del self.item_list[index]

    def __len__(self):
        return len(self.item_list)

    def __iter__(self):
        for index, value in enumerate(self.item_list):
            item = self._to_python(self.key, value)
            if isinstance(item, ld_container):
                item.index = index
            yield item

    def __contains__(self, value):
        expanded_value = self._to_expanded_json([value])
        if len(expanded_value) == 0:
            return True
        if len(expanded_value) > 1:
            return all(val in self for val in expanded_value)
        self_attributes = {"parent": self.parent, "key": self.key, "index": self.index, "context": self.full_context}
        if self.container_type == "@set":
            temp_list = ld_list(expanded_value, **self_attributes)
            return any(temp_list == ld_list([val], **self_attributes) for val in self.item_list)
        temp_list = ld_list([{self.container_type: expanded_value}], **self_attributes)
        return any(temp_list == ld_list([{self.container_type: [val]}], **self_attributes) for val in self.item_list)

    def __eq__(self, other):
        # TODO: ld_lists with container_type "@set" have to be considered unordered
        if not (isinstance(other, (list, ld_list)) or ld_list.is_container(other)):
            return NotImplemented
        if isinstance(other, dict):
            other = [other]
        if isinstance(other, list):
            if ld_list.is_ld_list(other):
                other = ld_list.get_item_list_from_container(other[0])
            other = self.from_list(other, parent=self.parent, key=self.key, context=self.context)
        if len(self.item_list) != len(other.item_list):
            return False
        if (self.key == "@type") ^ (other.key == "@type"):
            return False
        if self.key == other.key == "@type":
            return self.item_list == other.item_list
        for index, (item, other_item) in enumerate(zip(self.item_list, other.item_list)):
            if ((ld_container.is_typed_json_value(item) or ld_container.is_json_value(item)) and
                    (ld_container.is_typed_json_value(other_item) or ld_container.is_json_value(other_item))):
                if not ld_container.are_values_equal(item, other_item):
                    return False
                continue
            if "@id" in item and "@id" in other_item:
                return item["@id"] == other_item["@id"]
            item = self[index]
            other_item = other[index]
            res = item.__eq__(other_item)
            if res == NotImplemented:
                res = other_item.__eq__(item)
            if res is False or res == NotImplemented:  # res is not True
                return False
        return True

    def __ne__(self, other):
        x = self.__eq__(other)
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
