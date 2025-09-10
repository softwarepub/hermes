# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from .ld_container import ld_container


class ld_list(ld_container):
    """ An JSON-LD container resembling a list. """

    container_types = ['@list', '@set', '@graph']

    def __init__(self, data, *, parent=None, key=None, index=None, context=None):
        """ Create a new ld_list.py container.

        # FIXME: there is no parameter container
        :param container: The container type for this list.
        """
        # FIXME: A set container does not contain "@set" in the expected data format (expanded json ld)
        # Instead it is just a list of dicts and therefor would raise a ValueError here (and fail ld_list.is_ld_list)

        super().__init__(data, parent=parent, key=key, index=index, context=context)

        # Determine container and correct item list
        for container in self.container_types:
            if container in self._data[0]:
                self.item_list = self._data[0][container]
                self.container = container
                break
        else:
            raise ValueError(f"Unexpected dict: {data}")

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in [*range(len(self))][index]]

        item = self._to_python(self.key, [self.item_list[index]])
        if isinstance(item, ld_container):
            item.index = index
        return item

    def __setitem__(self, index, value):
        # FIXME: what should your_ld_list[index] = [{"@type": "foo", "name": "bar"}] mean?
        # set your_ld_list[index] to the dict {"@type": "foo", "name": "bar"} given in expanded form        or
        # set your_ld_list[index] to the list [{"@type": "foo", "name": "bar"}] given in non expanded form  or
        # set your_ld_list[index] to the set [{"@type": "foo", "name": "bar"}] given in expanded form
        #   (ld_list.fromlist([{"@type": "foo", "name": "bar"}]) defaults to container type list
        #    which would have the object as an expanded form whereas the expanded form of a list would be
        #    ["@list": [{"@type": "foo", "name": "bar"}]]
        #    This is relevent because nested sets get unnested when being expanded and lists not.
        #    Moreover a set inside a list gets automaticaly converted to a list when expanded)

        # FIXME: what happens when a ld_list is put inside another also depends on their container types

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
            item = self._to_python(self.key, [value])
            if isinstance(item, ld_container):
                item.index = index
            yield item

    def append(self, value):
        ld_value = self._to_expanded_json(self.key, value)
        self.item_list.extend(ld_value)

    def extend(self, value):
        for item in value:
            self.append(item)

    def to_python(self):
        # FIXME:
        # why is item not converted to it's python equivalent?
        #
        # ld_list([{"@list": [{"@value": "a"}]}])[0]
        #     == "a"
        # ld_list([{"@list": [{"@value": "a"}]}]).to_python()[0]
        #     == {"@value": "a"}                                                          why not "a"?
        # ld_list([{"@list": [ld_dict([{"@type": "Person", "name": "a"}])]}])[0]
        #     == ld_dict([{"@type": "Person", "name": "a"}])
        # ld_list([{"@list": [ld_dict([{"@type": "Person", "name": "a"}])]}]).to_python()[0]
        #     == {"@type": "Person", "name": "a"}
        #
        # ld_dict([{"name": [{"@value": "a"}]}])["name"] == "a"
        # ld_dict([{"name": [{"@value": "a"}]}]).to_python()["name"] == "a"               why not {"@value": "a"}?
        # ld_dict([{"person": [ld_dict([{"@type": "Person", "name": "a"}])]}])["person"]
        #     == ld_dict([{"@type": "Person", "name": "a"}])
        # ld_dict([{"person": [ld_dict([{"@type": "Person", "name": "a"}])]}]).to_python()["person"]
        #     == {"@type": "Person", "name": "a"}
        return [
            item.to_python() if isinstance(item, ld_container) else item
            for item in self
        ]

    @classmethod
    def is_ld_list(cls, ld_value):
        # FIXME: every python list that contains at least one dict can be considerd a set in expanded json form
        return cls.is_ld_node(ld_value) and cls.is_container(ld_value[0])

    @classmethod
    def is_container(cls, value):
        # FIXME: "@set" will never be inside a dictionary of an expanded json ld object
        return isinstance(value, dict) and any(ct in value for ct in cls.container_types)

    @classmethod
    def from_list(cls, value, *, parent=None, key=None, context=None, container=None):
        new_list = cls([{container or "@list": []}], parent=parent, key=key, context=context)
        new_list.extend(value)
        return new_list
