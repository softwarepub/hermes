import logging
import typing as t

from hermes.model.errors import MergeError
from hermes.model.path import ContextPath


class MergeBase:
    default_keys = []
    default_cast = {}

    def __init__(self, keys=None):
        self._keys = keys or self.default_keys
        self._log = logging.getLogger('hermes.merge')

    def __call__(self, path, target, value):
        updates = self.collect_updates(path, target, value)
        updates = self.check_updates(updates)

        self._log.debug(". %s changes to %s", len(updates), str(path))
        return updates

    def collect_updates(self, path, target, value):
        updates = []
        return updates

    def check_updates(self, updates):
        checked_updates = []

        for key, new_value, old_value in updates:
            if key is None:
                checked_updates.append((None, new_value, old_value))
                continue

            key = ContextPath.parse(key)
            cast = self.default_cast.get(('key', key.item), lambda x: x)
            if new_value is None or cast(old_value) == cast(new_value):
                continue
            elif old_value is None:
                checked_updates.append((key, new_value, old_value))

        return checked_updates

    def is_equal(self, left, right):
        if left.parent == right.parent and left.item == right.item:
            return True


class ObjectMerge(MergeBase):
    default_keys = ['@id']
    default_cast = {
        ('key', 'email'): str.upper,
    }

    def __call__(self, path, target, value):
        updates = super().__call__(path, target, value)
        merged_keys = []

        for subkey, new_value, old_value in updates:
            if subkey.item not in target:
                subkey.insert(target, new_value)
            else:
                subkey.update(target[subkey.item], new_value)

        return merged_keys

    def _active_keys(self, path, target, value):
        match value:
            case dict():
                value = [(path[_key], _value) for _key, _value in value.items()]
            case list():
                value = [(path[i], _value) for i, _value in enumerate(value)]
            case _:
                value = []

        return [
            (_key, _value, target if _key is None else target[_key])
            for _key, _value in value
            if _key is None or _key in target
        ]

    def collect_updates(self, path, target, value):
        _target, _prefix, _trace = path.resolve(target)
        updates = super().collect_updates(path, target, value)
        updates += self._active_keys(value, _target, value)
        return updates


class CollectionMerge(MergeBase):
    default_keys = ['@id']

    def __call__(self, path, target, value):
        updates = super().__call__(path, target, value)

        for _key, _old, _new in updates:
            self.default_cast[_key.item]()
            if _old is not None and _old != _new:
                raise MergeError(path, _old, _new)

            elif _new is not None and _old != _new:
                pass
