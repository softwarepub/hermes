import typing as t

import pyparsing as pp

from hermes import config

_log = config.getLogger('hermes.model.path')


class ContextPathGrammar:
    key = pp.Word('@' + pp.alphas)
    index = pp.Word(pp.nums).set_parse_action(lambda tok: [int(tok[0])]) | pp.Char('*')
    field = key + (pp.Suppress('[') + index + pp.Suppress(']'))[...]
    path = field + (pp.Suppress('.') + field)[...]

    @classmethod
    def parse(cls, text: str):
        return cls.path.parse_string(text)


class ContextPath:
    merge_strategies = None

    def __init__(self, item: str | int, parent: t.Optional['ContextPath'] = None):
        self._item = item
        self._parent = parent
        self._type = None

    @classmethod
    def init_merge_strategies(cls):
        if cls.merge_strategies is None:
            from hermes.model.merge import MergeStrategies, default_merge_strategies

            cls.merge_strategies = MergeStrategies()
            for strategy in default_merge_strategies:
                cls.merge_strategies.register(strategy)

    @property
    def parent(self) -> t.Optional['ContextPath']:
        return self._parent

    @property
    def path(self) -> t.List['ContextPath']:
        if self._parent is None:
            return [self]
        else:
            return self._parent.path + [self]

    def __getitem__(self, item: str | int) -> 'ContextPath':
        match item:
            case str(): self._type = dict
            case int(): self._type = list
        return ContextPath(item, self)

    def __str__(self) -> str:
        item = str(self._item)
        if self._parent is not None:
            parent = str(self._parent)
            match self._item:
                case '*' | int(): item = parent + f'[{item}]'
                case str(): item = parent + '.' + item
                case _: raise ValueError(self.item)
        return item

    def __repr__(self) -> str:
        return f'ContextPath.parse("{str(self)}")'

    def __eq__(self, other: 'ContextPath') -> bool:
        return (
            other is not None
            and (self._item == other._item or self._item == '*' or other._item == '*')
            and self._parent == other._parent
        )

    def __contains__(self, other: 'ContextPath') -> bool:
        while other is not None:
            if other == self:
                return True
            other = other.parent
        return False

    def new(self):
        if self._type is not None:
            return self._type()
        raise TypeError()

    @staticmethod
    def _get_item(target: dict | list, path: 'ContextPath') -> t.Optional['ContextPath']:
        match target, path._item:
            case list(), '*':
                raise IndexError(f'Cannot resolve any(*) from {path}.')
            case list(), int() as index if index < len(target):
                return target[index]
            case list(), int() as index:
                raise IndexError(f'Index {index} out of bounds for {path.parent}.')
            case list(), _ as index:
                raise TypeError(f'Invalid index type {type(index)} to access {path.parent}.')

            case dict(), str() as key if key in target:
                return target[key]
            case dict(), str() as key:
                raise KeyError(f'Key {key} not in {path.parent}.')
            case dict(), _ as key:
                raise TypeError(f'Invalid key type {type(key)} to access {path.parent}.')

            case _, _:
                raise TypeError(f'Cannot handle target type {type(target)} for {path}.')

    def _find_in_parent(self, target: dict, path: 'ContextPath') -> t.Any:
        _item = path._item
        _path = path.parent
        while _path is not None:
            try:
                item = self._get_item(target, _path[_item])
                _log.debug("Using type %s from §%s.", item, _path)
                return item

            except (KeyError, IndexError, TypeError) as e:
                _log.debug("%s: %s", _path, e)
                _path = _path.parent
                continue

        return None

    def _find_setter(self, target: dict | list, path: 'ContextPath', value: t.Any = None, **kwargs) -> t.Callable:
        filter = {
            'name': path._item,
        }

        if isinstance(path._item, str) or path._parent is not None:
            filter['path'] = str(path)

        if type := self._find_in_parent(target, path['@type']):
            filter['type'] = type
        elif value is not None:
            match value:
                case list(): filter['type'] = 'list'
                case dict(): filter['type'] = 'map'
        elif path._type is list:
                filter['type'] = 'list'
        elif path._type is dict:
                filter['type'] = 'map'

        if ep := kwargs.get('ep', None):
            filter['ep'] = ep

        setter = self.merge_strategies.select(**filter)
        if setter is None:
            return self._set_item
        else:
            return setter

    def _set_item(self, target: dict | list, path: 'ContextPath', value: t.Any, **kwargs) -> t.Optional['ContextPath']:
        match target, path._item:
            case list(), int() as index if index < len(target):
                match target[index]:
                    case dict() as t: t.update(value)
                    case list() as l: l[:] = value
                    case _: target[index] = value

            case dict(), str() as key if key in target:
                match target[key]:
                    case dict() as t: t.update(value)
                    case list() as l: l[:] = value
                    case _: target[key] = value

            case dict(), str() as key:
                target[key] = value
            case list(), '*':
                path._item = len(target)
                target.append(value)
            case list(), int() as index if index == len(target):
                target.append(value)

            case dict(), _ as key:
                raise TypeError(f'Invalid key type {type(key)} to set in {path.parent}.')
            case list(), int() as index:
                raise IndexError(f'Index {index} out of bounds to set in {path.parent}.')
            case list(), _ as index:
                raise TypeError(f'Invalid index type {type(index)} to set in {path.parent}.')

            case _, _:
                raise TypeError(f'Cannot handle target type {type(target)} to set {path}.')

        return value

    def resolve(self, _target: list | dict, create: bool = False, query: t.Any = None) -> ('ContextPath', list | dict, 'ContextPath'):
        head, *tail = self.path
        target = _target
        while head._type and tail:
            try:
                target = self._get_item(target, head)
            except (IndexError, KeyError, TypeError):
                if create and self.parent is not None:
                    new_head = head.new()
                    setter = self._find_setter(_target, head, new_head)
                    setter(target, head, new_head)
                    target = new_head
                else:
                    break
            head, *tail = tail

        if head._item == '*':
            for i, item in enumerate(target):
                if all(item[k] == v for k, v in query.items() if k in item):
                    head._item = i
                    break
            else:
                if create:
                    head._item = len(target)

        if not hasattr(head, 'set_item'):
            head.set_item = self._find_setter(_target, head)
        tail_path = ContextPath(head._item)
        for t in tail:
            tail_path = tail_path[t._item]

        return head, target, tail_path

    def get_from(self, target: dict | list) -> t.Any:
        prefix, target, path = self.resolve(target)
        return self._get_item(target, path)

    def update(self, target: t.Dict[str, t.Any] | t.List, value: t.Any, tags: t.Optional[dict] = None, **kwargs):
        prefix, target, tail = self.resolve(target, create=True)
        prefix.set_item(target, tail, value, **kwargs)
        if tags is not None and kwargs:
            tags[str(self)] = kwargs

    @classmethod
    def parse(cls, path: str) -> 'ContextPath':
        head, *tail = ContextPathGrammar.parse(path)
        path = cls(head)
        for item in tail:
            path = path[item]
        return path
