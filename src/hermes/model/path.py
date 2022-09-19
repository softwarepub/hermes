import typing as t

from hermes import config
from hermes.model.errors import MergeError


_log = config.getLogger('hermes.model')


class MergeRunner:
    _registry = {}

    def __init__(self, strategies):
        self._strategies = strategies
        _log.debug(". Loaded %d strategies", len(self._strategies))

    def __call__(self, path, target, value, **kwargs):
        merged_keys = []

        for merge in self._strategies:
            try:
                print(path, target, value)
                _log.info(". Trying merge using %s", merge)
                result = merge(path, target, value, **kwargs)

            except MergeError as e:
                _log.warning("! %s failed:", merge)
                _log.info("> %s", e)
                continue

            else:
                merged_keys.extend(result)
                break

        else:
            return False

        return merged_keys

    def compare(self, path, other):
        if other is not None and path.item == other.item and path.parent == other.parent:
            return True
        return False

    @classmethod
    def _filter_matches(cls, filter, kwargs):
        for key, value in filter.items():
            print(key, value, kwargs)
            if key not in kwargs or kwargs[key] in value:
                return True

        return False

    @classmethod
    def register(cls, name, merge, **kwargs):
        cls._registry[name or str(merge)] = (kwargs, merge)

    @classmethod
    def query(cls, **kwargs):
        strategies = []
        for filter, strategy in cls._registry.values():
            if cls._filter_matches(filter, kwargs):
                strategies.append(strategy)

        return cls(strategies)


class ContextPath:
    def __init__(self, item: str | int, parent: t.Optional['ContextPath'] = None):
        self._item = item
        self._parent = parent
        self._type = None

    @property
    def parent(self) -> t.Optional['ContextPath']:
        return self._parent

    @property
    def item(self) -> t.Optional[str | int]:
        return self._item

    @property
    def is_container(self):
        return self._type in (list, dict)

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
        if (other is None) or (self.parent != other.parent) \
                or (self.item != '*' and other.item != '*' and self.item != other.item):
            return False

        return True

    def __contains__(self, other: 'ContextPath') -> bool:
        while other is not None:
            if other == self:
                return True
            other = other.parent
        return False

    def _get_trace(self):
        if self.parent:
            return self.parent._get_trace() + [self._item]
        else:
            return [self._item]

    def new(self):
        return self._type()

    def _select_from(self, _target, _head, *_trace):
        _prefix = self[_head]

        match _target, _head:
            case list(), int() if len(_target) > _head:
                if _trace:
                    _target, _prefix, _trace = _prefix._select_from(_target[_head], *_trace)
                else:
                    _target = _target[_head]

            case dict(), str() if _head in _target:
               if _trace:
                   _target, _prefix, _trace = _prefix._select_from(_target[_head], *_trace)
               else:
                   _target = _target[_head]

            case (list(), '*' | int()) | (dict(), str()):
                pass

            case _, _:
                raise KeyError(_target, _head)

        return _target, _prefix, _trace

    def _set_in_target(self, _target, value):
        match _target:
            case list():
                if self.item == '*' or self.item == len(_target):
                    self._item = len(_target)
                    _target.append(value)
                elif self.item > len(_target):
                    raise IndexError()
                else:
                    # TODO use update instead of replace...
                    _target[self._item] = value

            case dict():
                if self.item not in _target:
                    _target[self._item] = value
                else:
                    # TODO use update instead of replace...
                    _target[self._item] = value

            case _:
                raise TypeError()

    def resolve(self, target):
        _head, *_trace = self._get_trace()
        _prefix = ContextPath(_head)
        _target = target

        if _head not in target:
            tail = [_prefix]
            for item in _trace:
                tail.append(tail[-1][item])

        return _prefix._select_from(target, _head, *_trace)

    def select(self, target: t.Dict | t.List) -> 'ContextPath':
        head, *trace = self._get_trace()
        if head in target:
            _, _prefix, _ = ContextPath(head)._select_from(target[head], *trace)
        else:
            _prefix = None
        return _prefix

    def update(self, target: t.Dict[str, t.Any] | t.List, value: t.Any, **kwargs: t.Any):
        _head, *_trace = self._get_trace()
        _target = target
        _prefix = ContextPath(_head)

        if _head in target:
            _target, _prefix, _trace = ContextPath(_head)._select_from(target[_head], *_trace)

        if _head not in _target:
            _prefix.insert(_target, value, **kwargs)

        q = {'path': str(self)}
        if _prefix._type is list: q['type'] = 'list'
        if _prefix._type is dict: q['type'] = 'map'
        print(_prefix, _prefix._type, q)

        merge_runner = MergeRunner.query(**q)
        return merge_runner(self, _target, value, **kwargs)

    def insert(self, target, value, **kwargs):
        keys_added = []
        _target, _prefix, _trace = self.resolve(target)

        while _prefix.is_container:
            _prefix._set_in_target(_target, _prefix.new())
            _target = _target[_prefix.item]

        _prefix._set_in_target(_target, value)

        return keys_added

    @classmethod
    def parse(cls, path: str) -> 'ContextPath':
        full_path = None
        for part in path.split('.'):
            name, _, index = part.partition('[')

            if full_path is None:
                full_path = ContextPath(name)
            else:
                full_path = full_path[name]

            if not index: continue

            for idx in index[:-1].split(']['):
                try:
                    idx = int(idx)
                except ValueError:
                    pass
                finally:
                    full_path = full_path[idx]

        return full_path


class query_dict:
    def __init__(self, data=None, **kwargs):
        self.data = data or {}
        self.data.update(**kwargs)

    def __contains__(self, item):
        return all(self.data.get(k) == v for k, v in item.items())

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)


if __name__ == '__main__':
    from hermes.commands.process.merge import ObjectMerge, CollectionMerge

    MergeRunner.register('default', ObjectMerge(['@id', 'email', 'name']), )

    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    class query_dict:
        def __init__(self, data=None, **kwargs):
            self.data = data or {}
            self.data.update(**kwargs)

        def __contains__(self, item):
            return all(self.data.get(k) == v for k, v in item.items())

        def __repr__(self):
            return repr(self.data)

        def __str__(self):
            return str(self.data)

    data = {
        'author': [
            {'@type': ['Person', 'hermes:contributor'], 'name': 'Michael Meinel', 'email': 'michael.meinel@DLR.de'},
            {'@type': 'Person', 'name': 'Stephan Druskat'},
        ]
    }


    author = ContextPath('author')
    author[0].update(data, {'givenName': 'Michael', 'familyName': 'Meinel', 'email': "Michael.Meinel@dlr.de"}, ep='git', stage='harvest')
    author[1].update(data, {'email': 'spam@egg.com'})

    print(data)
