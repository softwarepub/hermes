from .ld_container import ld_container


class ld_list(ld_container):
    """ An JSON-LD container resembling a list. """

    container_types = ['@list', '@set', '@graph']

    def __init__(self, data, *, parent=None, key=None, index=None, context=None):
        """ Create a new ld_list.py container.

        :param container: The container type for this list.
        """

        super().__init__(data, parent=parent, key=key, index=index, context=context)

        # Determine container and correct item list
        for container in self.container_types:
            if container in self._data[0]:
                self.item_list = self._data[0][container]
                self.container = container
                break
        else:
            raise ValueError(f"Unexpected dict: {self.data}")

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in [*range(len(self))][index]]

        item = self._to_python(self.key, self.item_list[index:index + 1])
        if isinstance(item, ld_container):
            item.index = index
        return item

    def __setitem__(self, index, value):
        self.item_list[index:index + 1] = self._to_expanded_json(self.key, value)

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
        return [
            item.to_python() if isinstance(item, ld_container) else item
            for item in self
        ]

    @classmethod
    def is_ld_list(cls, ld_value):
        return cls.is_ld_node(ld_value) and cls.is_container(ld_value[0])

    @classmethod
    def is_container(cls, value):
        return isinstance(value, dict) and any(ct in value for ct in cls.container_types)

    @classmethod
    def from_list(cls, value, *, parent=None, key=None, context=None, container=None):
        new_list = cls([{container or "@list": []}], parent=parent, key=key, context=context)
        new_list.extend(value)
        return new_list
