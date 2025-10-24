# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

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
        # FIXME: #439 what should your_ld_list[index] = [{"@type": "foo", "name": "bar"}] mean?
        # set your_ld_list[index] to the dict {"@type": "foo", "name": "bar"} given in expanded form        or
        # set your_ld_list[index] to the list [{"@type": "foo", "name": "bar"}] given in non expanded form

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
        if isinstance(other, ld_list):
            # FIXME: #439 When are ld_lists equal?
            return self.item_list == other.item_list
        if isinstance(other, list):
            if ld_list.is_ld_list(other):
                other = ld_list.get_item_list_from_container(other)
            return self.item_list == self.from_list(other, key=self.key, context=self.full_context).item_list
        return NotImplemented

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
