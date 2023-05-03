# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from hermes.model.path import ContextPath, set_in_dict


class MergeStrategies:
    def __init__(self):
        self._strategies = []

    def select(self, **kwargs):
        fitting_strategies = [
            strategy
            for strategy in self._strategies
            if strategy.can_handle(kwargs)
        ]
        if fitting_strategies:
            return fitting_strategies[0]
        else:
            return None

    def register(self, strategy):
        self._strategies.append(strategy)


class MergeStrategy:
    @staticmethod
    def _check_types(item, value):
        match item:
            case list(): return any(t in value for t in item)
            case str(): return item in value
        return False

    @staticmethod
    def _check_path(item, value):
        item = ContextPath.parse(item)
        value = ContextPath.parse(value)
        if item == value or item in value:
            return True
        return False

    checks = {
        'type': _check_types,
        'path': _check_path,
    }

    def __init__(self, **filter):
        self._filter = filter

    def _check(self, key, filter, value):
        if key in filter:
            check = self.checks.get(key, lambda item, value: item in value)
            return check(filter[key], value)
        return True

    def can_handle(self, filter: dict):
        return all(
            self._check(key, filter, value)
            for key, value in self._filter.items()
        )

    def are_equal(self, left, right):
        return left == right


class CollectionMergeStrategy(MergeStrategy):
    def __init__(self, **filter):
        super().__init__(**filter)

    def are_equal(self, left, right):
        return all(
            any(a == b for b in right)
            for a in left
        )

    def __call__(self, target, path, value, **kwargs):
        match target, path._item:
            case list(), int() as index if index < len(target):
                match target[index]:
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: target[index] = value

            case list(), '*':
                path._item = len(target)
                target.append(value)

            case list(), int() as index if index == len(target):
                target.append(value)

            case list(), int() as index:
                raise IndexError(f'Index {index} out of bounds to set in {path.parent}.')
            case list(), _ as index:
                raise TypeError(f'Invalid index type {type(index)} to set in {path.parent}.')

            case dict(), str() as key if key in target:
                match target[key]:
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: set_in_dict(target, key, value, kwargs)

            case dict(), str() as key:
                target[key] = value

            case dict(), _ as key:
                raise TypeError(f'Invalid key type {type(key)} to set in {path.parent}.')

            case _, _:
                raise TypeError(f'Cannot handle target type {type(target)} to set {path}.')

        return value


class ObjectMergeStrategy(MergeStrategy):
    def __init__(self, *id_keys, **filter):
        super().__init__(**filter)
        self.id_keys = id_keys or ('@id', )

    def are_equal(self, left, right):
        if not self.id_keys:
            return super().are_equal(left, right)
        else:
            return any(left[key] == right[key] for key in self.id_keys if key in left and key in right)

    def __call__(self, target, path, value, **kwargs):
        match target, path._item:
            case dict(), str() as key if key in target:
                match target[key]:
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: set_in_dict(target, key, value, kwargs)

            case dict(), str() as key:
                target[key] = value

            case dict(), _ as key:
                raise TypeError(f'Invalid key type {type(key)} to set in {path.parent}.')

            case list(), int() as index if index < len(target):
                match target[index]:
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: target[index] = value

            case list(), '*':
                path._item = len(target)
                target.append(value)

            case list(), int() as index if index == len(target):
                target.append(value)

            case list(), int() as index:
                raise IndexError(f'Index {index} out of bounds to set in {path.parent}.')
            case list(), _ as index:
                raise TypeError(f'Invalid index type {type(index)} to set in {path.parent}.')

            case _, _:
                raise TypeError(f'Cannot handle target type {type(target)} to set {path}.')

        return value


default_merge_strategies = [
    ObjectMergeStrategy(
        '@id', 'email', 'name',
        path='author[*]',
    ),

    CollectionMergeStrategy(
        type=['list'],
    ),

    ObjectMergeStrategy(
        type=['map'],
    )
]
