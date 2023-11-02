# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import logging
import typing as t

import pyparsing as pp

from hermes.model import errors

_log = logging.getLogger('hermes.model.path')


def set_in_dict(target: dict, key: str, value: object, kwargs):
    if target[key] != value:
        tag = kwargs.pop('tag', {})
        alt = tag.pop('alternatives', [])
        alt.append((target[key], tag.copy()))
        tag.clear()
        tag['alternatives'] = alt
    target[key] = value


class ContextPathGrammar:
    """
    The pyparsing grammar for ContextGrammar paths.
    """

    key = pp.Word('@:_' + pp.alphas)
    index = pp.Word(pp.nums).set_parse_action(lambda tok: [int(tok[0])]) | pp.Char('*')
    field = key + (pp.Suppress('[') + index + pp.Suppress(']'))[...]
    path = field + (pp.Suppress('.') + field)[...]

    @classmethod
    def parse(cls, text: str) -> pp.ParseResults:
        """
        Parse a ContextPath string representation into its individual tokens.

        :param text: The path to parse.
        :return: The pyparsing.ParseResult.
        """
        return cls.path.parse_string(text)


class ContextPath:
    """
    This class is used to access the different contexts.

    On the one hand, the class allows you to define and manage paths.
    You can simply build them up like follows:

    >>> path = ContextPath('spam')['eggs'][1]['ham']

    will result in a `path` like `spam.eggs[1].ham`.

    hint ::
        The paths are idenpendent from any context.
        You can create and even re-use them independently for different contexts.

        To construct wildcard paths, you can use the `'*'` as accessor.

    If you need a shortcut for building paths from a list of accessors, you can use :py:meth:`ContextPath.make`.
    To parse the string representation, use :py:meth:`ContextPath.parse`.
    """

    merge_strategies = None

    def __init__(self, item: str | int | t.List[str | int], parent: t.Optional['ContextPath'] = None):
        """
        Initialize a new path element.

        The path stores a reference to it's parent.
        This means that

        >>> path ContextPath('foo', parent=ContextPath('bar'))

        will result in the path `bar.foo`.

        :param item: The accessor to the current path item.
        :param parent: The path of the parent item.
        """
        if isinstance(item, (list, tuple)) and item:
            *head, self._item = item
            if head:
                self._parent = ContextPath(head, parent)
            else:
                self._parent = parent
        else:
            self._item = item
            self._parent = parent
        self._type = None

    @classmethod
    def init_merge_strategies(cls):
        # TODO refactor
        if cls.merge_strategies is None:
            from hermes.model.merge import MergeStrategies, default_merge_strategies

            cls.merge_strategies = MergeStrategies()
            for strategy in default_merge_strategies:
                cls.merge_strategies.register(strategy)

    @property
    def parent(self) -> t.Optional['ContextPath']:
        """
        Accessor to the parent node.
        """
        return self._parent

    @property
    def path(self) -> t.List['ContextPath']:
        """
        Get the whole path from the root as list of items.
        """
        if self._parent is None:
            return [self]
        else:
            return self._parent.path + [self]

    def __getitem__(self, item: str | int) -> 'ContextPath':
        """
        Create a sub-path for the given `item`.
        """
        match item:
            case str(): self._type = dict
            case int(): self._type = list
        return ContextPath(item, self)

    def __str__(self) -> str:
        """
        Get the string representation of the path.
        The result is parsable by :py:meth:`ContextPath.parse`
        """
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
        """
        This match includes semantics for wildcards.
        Items that access `'*'` will automatically match everything (except for None).
        """
        return (
            other is not None
            and (self._item == other._item or self._item == '*' or other._item == '*')
            and self._parent == other._parent
        )

    def __contains__(self, other: 'ContextPath') -> bool:
        """
        Check whether `other` is a true child of this path.
        """
        while other is not None:
            if other == self:
                return True
            other = other.parent
        return False

    def new(self) -> t.Any:
        """
        Create a new instance of the container this node represents.

        For this to work, the node need to have at least on child node derive (e.g., by using ``self["child"]``).
        """
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
                _log.debug("Using type %s from %s.", item, _path)
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
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: target[index] = value

            case dict(), str() as key if key in target:
                match target[key]:
                    case dict() as item: item.update(value)
                    case list() as item: item[:] = value
                    case _: set_in_dict(target, key, value, kwargs)

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

    def resolve(self,
                target: list | dict,
                create: bool = False,
                query: t.Any = None) -> ('ContextPath', list | dict, 'ContextPath'):
        """
        Resolve a given path relative to a given target.

        The method will incrementally try to resolve the entries in the `_target.path`.
        It stops when the requested item was found or when the resolution could not be completed.
        If you set `create` to true, the method tries to create the direct target that contains the selected node.

        :param target: Container to resolve node in.
        :param create: Flags whether missing containers should be created.
        :param query:
        :return: The method returns a tuple with the following values:
            - The path to the last item that could be resolved (e.g., the container of the requested element).
            - The container for the path from the first return value.
            - The rest of the path that could not be resolved.
        """
        head, *tail = self.path
        next_target = target
        while tail:
            try:
                new_target = self._get_item(next_target, head)
                if not isinstance(new_target, (list, dict)) and head.parent:
                    next_target = self._get_item(next_target, head.parent)
                    tail = [head._item] + tail
                    break
                else:
                    next_target = new_target
            except (IndexError, KeyError, TypeError):
                if create and self.parent is not None:
                    try:
                        new_target = head.new()
                    except TypeError:
                        pass
                    else:
                        setter = self._find_setter(target, head, new_target)
                        setter(next_target, head, new_target)
                        next_target = new_target
                else:
                    break
            head, *tail = tail

        if head._item == '*':
            for i, item in enumerate(next_target):
                _keys = [k for k in query.keys() if k in item]
                if _keys and all(item[k] == query[k] for k in _keys):
                    head._item = i
                    break
            else:
                if create:
                    head._item = len(next_target)

        if not hasattr(head, 'set_item'):
            head.set_item = self._find_setter(target, head)
        tail = ContextPath.make([head._item] + tail)
        return head, next_target, tail

    def get_from(self, target: dict | list) -> t.Any:
        """
        Expand the path and return the referenced data from a concrete container.

        :param target: The list or dict that this path points into.
        :return: The value stored at path.
        """
        prefix, target, path = self.resolve(target)
        return self._get_item(target, path)

    def update(self, target: t.Dict[str, t.Any] | t.List, value: t.Any, tags: t.Optional[dict] = None, **kwargs):
        """
        Update the data stored at the path in a concrete container.

        How this method actually behaves heavily depends on the active MergeStrategy for the path.

        :param target: The dict inside which the value should be stored.
        :param value: The value to store.
        :param tags: Dictionary containing the tags for all stored values.
        :param kwargs: The tag attibutes for the new value.
        """
        prefix, _target, tail = self.resolve(target, create=True)
        try:
            _tag = {}
            if tags:
                if str(self) in tags:
                    _tag = tags[str(self)]
                else:
                    tags[str(self)] = _tag

            prefix.set_item(_target, tail, value, tag=_tag, **kwargs)
            if tags is not None and kwargs:
                _tag.update(kwargs)

        except (KeyError, IndexError, TypeError, ValueError):
            raise errors.MergeError(self, _target, value, **kwargs)

    @classmethod
    def make(cls, path: t.Iterable[str | int]) -> 'ContextPath':
        """
        Convert a list of item accessors into a ContextPath.

        :param path: The items in the order of access.
        :return: A ContextPath that reference the selected value.
        """
        head, *tail = path
        path = ContextPath(head)
        for next in tail:
            path = path[next]
        return path

    @classmethod
    def parse(cls, path: str) -> 'ContextPath':
        """
        Parse a string representation of a ContextPath into a proper object.

        :param path: The path to parse.
        :return: A new ContextPath that references the selected path.
        """
        path = cls.make(ContextPathGrammar.parse(path))
        return path
