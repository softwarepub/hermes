# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from .ld_container import ld_container


class ld_list(ld_container):
    """ An JSON-LD container resembling a list. """

    def __init__(self, data, *, parent=None, key=None, index=None, context=None):
        if not (self.is_ld_list(data) and "@list" in data[0]):
            raise ValueError("The given data does not represent a ld_list.")
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        self.item_list = data[0]["@list"]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in [*range(len(self))][index]]

        item = self._to_python(self.key, self.item_list[index])
        if isinstance(item, ld_container):
            item.index = index
        return item

    def __setitem__(self, index, value):
        if not isinstance(index, slice):
            self.item_list[index] = val[0] if isinstance(val := self._to_expanded_json(self.key, value), list) else val
            return
        try:
            iter(value)
        except TypeError as exc:
            raise TypeError("must assign iterable to extended slice") from exc
        expanded_value = [self._to_expanded_json(self.key, val) for val in value]
        self.item_list[index] = [val[0] if isinstance(val, list) else val for val in expanded_value]

    def __len__(self):
        return len(self.item_list)

    def __iter__(self):
        for index, value in enumerate(self.item_list):
            item = self._to_python(self.key, value)
            if isinstance(item, ld_container):
                item.index = index
            yield item

    def __contains__(self, value):
        expanded_value = val[0] if isinstance(val := self._to_expanded_json(self.key, value), list) else val
        return expanded_value in self.item_list

    def __eq__(self, other):
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
        ld_value = self._to_expanded_json(self.key, value)
        self.item_list.extend(ld_value)

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
    def from_list(cls, value, *, parent=None, key=None, context=None):
        new_list = cls([{"@list": []}], parent=parent, key=key, context=context)
        new_list.extend(value)
        return new_list

    @classmethod
    def get_item_list_from_container(cls, ld_value):
        for cont in {"@list", "@set", "@graph"}:
            if cont in ld_value:
                return ld_value[cont]
        raise ValueError("The given data does not represent a container.")
