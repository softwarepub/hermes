import json
import pathlib
import typing as t
import uuid
from pprint import pprint

from frozendict import frozendict

from hermes.model.ld_types.pyld_util import jsonld, JsonLdProcessor


class LD_container:
    """ Base class that hides the expanded form of a JSON-LD dataset. """

    KEYWORDS = jsonld.KEYWORDS

    _default_context = frozendict({
        '_uuid': str(uuid.uuid1()),
        'processingMode': 'json-ld-1.1',
        'mappings': {}
    })

    ld_proc = JsonLdProcessor()

    def __init__(self,
                 data: t.Any,
                 parent: t.Any = None,
                 key: t.Union[str, int, None] = None,
                 context: t.Optional[t.List[t.Union[str, t.Dict[str, t.Any]]]] = None):

        self.data = data
        self.parent = parent
        self.context = context
        self.default_context = self.ld_proc.process_context(
            LD_container._default_context, self.full_context, {})

        self.key = self._expand_iri(key) if isinstance(key, str) else key

    @property
    def full_context(self):
        full_context = self.parent.full_context[:] if self.parent else []
        if self.context:
            full_context.extend(ctx for ctx in self.context if ctx not in full_context)
        return full_context

    @property
    def full_path(self):
        if self.parent is None:
            return ['$']

        key = self.key
        if isinstance(key, str):
            key = self._compact_iri(key)
        return [*self.parent.full_path, key]

    def _expand_iri(self, short_iri: str) -> str:
        expanded_iri = self.ld_proc.expand_iri(short_iri, self.default_context)
        return expanded_iri

    def _expand_value(self, key: t.Union[str, int], value: t.Any):
        if isinstance(value, LD_container):
            value = value.data
        elif isinstance(value, dict):
            value, *_ = self.ld_proc.expand(value, {'expandContext': self.full_context})
        elif isinstance(value, list):
            value = [self._expand_value(i, val) for i, val in enumerate(value)]
        elif key not in self.KEYWORDS:
            if isinstance(key, str):
                key = self._compact_iri(key)
            value = [{'@value': value}]

        return value

    def _compact_iri(self, full_iri: str):
        compact_iri = self.ld_proc.compact_iri(full_iri, self.default_context)
        return compact_iri

    def _compact_value(self, key: t.Union[str, int], value: t.Any):
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if isinstance(value, dict):
            if '@type' in value:
                value = LD_dict(value, parent=self, key=key)
            elif '@value' in value:
                value = value['@value']
                if isinstance(key, str):
                    key = self._compact_iri(key)
            elif '@id' in value:
                value = self._compact_iri(value['@id'])
            elif '@list' in value:
                value = LD_list(value, parent=self, key=key)
            else:
                value = LD_dict(value, parent=self, key=key)

        elif isinstance(value, list):
            value = LD_list(value, parent=self, key=key)

        elif key == '@type':
            value = self._compact_iri(value)

        return value

    @classmethod
    def from_file(cls, path: pathlib.Path) -> t.Self:
        json_data = json.load(path.open('rb'))
        expanded = cls.ld_proc.expand(json_data, {})
        return cls(expanded[0], context=json_data.get('@context', None))

    def compact_data(self):
        yield NotImplementedError()

    def __repr__(self):
        return repr(self.compact_data())

    def __str__(self):
        return str(self.compact_data())


class LD_list(LD_container):
    """ Container for a list of entries. """

    def __init__(self,
                 data: t.Any,
                 parent: t.Optional[LD_container] = None,
                 key: t.Union[str, int, None] = None,
                 context: t.Optional[t.Dict[str, t.Any]] = None):

        super().__init__(data, parent, key, context)
        self._data_list = data if isinstance(data, list) else data['@list']

    def __len__(self):
        return len(self._data_list)

    def __getitem__(self, index: t.Union[int, slice]):
        internal_value = self._data_list[index]
        return self._compact_value(index, internal_value)

    def __setitem__(self, index: t.Union[int, slice], value: t.Any):
        internal_value = self._expand_value(index, value)
        self._data_list[index] = internal_value

    def __iter__(self):
        for i, v in enumerate(self._data_list):
            yield self._compact_value(i, v)

    def append(self, value: t.Any):
        internal_value = self._expand_value(len(self), value)
        if isinstance(internal_value, list):
            self._data_list.extend(internal_value)
        else:
            self._data_list.append(internal_value)

    def compact_data(self):
        return [*self]

    @classmethod
    def from_items(cls,
                    *items,
                   parent: t.Optional[LD_container] = None,
                   key: t.Any = None,
                   context: t.Any = None,
                   container: str = None):

        if container:
            list_data = {container: []}
        else:
            list_data = []

        ld_list = LD_list(list_data, parent, key, context)
        for item in items:
            ld_list.append(item)

        return ld_list


class LD_dict(LD_container):
    """ Container for an object. """

    _NOT_SET = type(False)

    @property
    def ld_type(self):
        return self.get('@type', None)

    def __contains__(self, key: str):
        full_iri = self._expand_iri(key)
        return full_iri in self.data

    def get(self, key: str, default: t.Any = _NOT_SET):
        key = self._expand_iri(key)

        if key in self:
            return self[key]
        elif default is not LD_dict._NOT_SET:
            return default
        else:
            raise KeyError(key)

    def __getitem__(self, key: str):
        key = self._expand_iri(key)
        internal_value = self.data[key]
        return self._compact_value(key, internal_value)

    def __setitem__(self, key: str, value: t.Any):
        key = self._expand_iri(key)
        internal_value = self._expand_value(key, value)
        self.data[key] = internal_value

    def keys(self):
        for key in self.data.keys():
            yield self._compact_iri(key)

    def items(self):
        for key, value in self.data.items():
            yield self._compact_iri(key), self._compact_value(key, value)

    def compact_data(self):
        result = {k: v for k, v in self.items()}
        if self.context:
            result['@context'] = self.context
        return result

    def compact_jsonld(self, context=None):
        context = context or self.full_context
        return self.ld_proc.compact(self.data, context, {})

    @classmethod
    def from_dict(cls, data: t.Dict) -> t.Self:
        expanded = cls.ld_proc.expand(data, {})
        return cls(expanded[0], context=data.get('@context', None))


if __name__ == '__main__':
    full_data = {}
    new_data = LD_dict(full_data, context=["https://doi.org/10.5063/schema/codemeta-2.0"])

    new_data["type"] = "SoftwareSourceCode"
    new_data["name"] = "test-data"
    new_data["version"] = "1.0.0"
    new_data["author"] = LD_list.from_items(
        {"type": "Person", "name": "Generic Bot", "email": "foo@example.com"},
        {"type": "Person", "name": "Generic Bot 2", "email": "bar@example.com"},
        {"type": "Person", "name": "Generic Botttttt", "email": "baz@example.com"},
        parent=new_data, key="author", container="@list"
    )
    new_data["author"][0]["affiliation"] = {"type": "Organization", "name": "ACME Corp."}
    new_data["keywords"] = LD_list.from_items("foo", "bar", parent=new_data, key="keywords")

    pprint(new_data.compact_jsonld())
