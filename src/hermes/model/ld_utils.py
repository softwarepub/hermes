import json
import logging
import pathlib
import typing as t

from pyld import jsonld


_log = logging.getLogger('hermes.model')


def bundled_document_loader(
        base_dir: pathlib.Path = pathlib.Path(__file__).parent / 'schemas',
        base_loader: t.Optional[t.Callable] = None,
        preload: bool = False
) -> t.Callable:
    if base_loader is None:
        base_loader = jsonld.get_document_loader()

    loaded_schemas = [
    ]

    def _load_schema(url, name):
        filename = base_dir / f'{name}.jsonld'
        with filename.open('r', encoding='utf-8') as f:
            loaded_schemas.append({
                'contentType': 'application/ld+json',
                'contextUrl': None,
                'documentUrl': url,
                'document': json.load(f)
            })

    if preload:
        _load_schema('https://schema.org', 'schemaorg-current-https'),
        _load_schema('http://schema.org', 'schemaorg-current-http'),
        _load_schema('https://doi.org/10.5063/schema/codemeta-2.0', 'codemeta'),
        _load_schema('https://schema.software-metadata.pub/hermes-git/1.0', 'hermes-git')

    def _load_bundled_document(url, options={}):
        for schema in loaded_schemas:
            if url.startswith(schema['documentUrl']):
                return schema

        return base_loader(url, options)

    return _load_bundled_document


jsonld.set_document_loader(bundled_document_loader(preload=True))


class jsonld_dict(dict):
    COMMON_CONTEXT = [
        'https://doi.org/10.5063/schema/codemeta-2.0',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not '@context' in self:
            self._context = self.COMMON_CONTEXT[:]
            self['@context'] = self._context
        else:
            self._context = self['@context']
            _log.warning("Skipping default context as a context is already given: %s", self['@context'])

    def _unmap(self, value):
        if isinstance(value, list):
            if len(value) > 1:
                raise ValueError("Ambiguous")
            value = value[0]
        if isinstance(value, dict):
            if '@value' in value:
                value = self._unmap(value["@value"])
            elif '@list' in value:
                value = self._wrap(value['@list'])

        if isinstance(value, dict):
            value = jsonld_dict(**value)

        return value

    def _wrap(self, item):
        if isinstance(item, list):
            return [
                jsonld_dict(**v) if isinstance(v, dict) else v
                for v in item
            ]
        elif isinstance(item, dict):
            return jsonld_dict(**item)
        else:
            return item

    def __getitem__(self, item):
        iri, mode = item

        value = self.get(iri, None)
        if mode == 'jsonld':
            return self._wrap(value)
        elif mode == 'value':
            return self._unmap(value)

    def add_context(self, context):
        if not isinstance(self._context, list):
            self._context = [self._context]
            self['@context'] = self._context
        self._context.append(context)

    def expand(self):
        return jsonld.expand(self), self._context

    @classmethod
    def with_extra_context(cls, **kwargs):
        self = cls()
        self.add_context(kwargs)
        return self

    @classmethod
    def from_file(cls, path: pathlib.Path):
        data = json.load(path.open("r"))
        if isinstance(data, list):
            if len(data) > 1:
                raise ValueError("Data is not a dict.")
            data = data[0]
        return cls(**data)


class ValueAccess:
    def __init__(self, linked_data: jsonld_dict):
        self._data = linked_data

    def term_to_iri(self, term):
        res, *_ = jsonld.expand({term: {}, '@context': self._data.get('@context')})
        key, *_ = res.keys()
        return key

    def __getitem__(self, term):
        item = self._data[self.term_to_iri(term), 'value']
        if isinstance(item, list):
            item = [ValueAccess(v) if isinstance(v, jsonld_dict) else v for v in item]
        elif isinstance(item, jsonld_dict):
            item = ValueAccess(item)
        return item


class JSONLDAccess:
    def __init__(self, linked_data: jsonld_dict):
        self._data = linked_data

    def __getitem__(self, iri):
        item = self._data[iri, 'jsonld']
        if isinstance(item, list):
            item = [JSONLDAccess(v) if isinstance(v, jsonld_dict) else v for v in item]
        elif isinstance(item, jsonld_dict):
            item = JSONLDAccess(item)
        return item


if __name__ == '__main__':
    data = jsonld_dict.from_file(pathlib.Path(".hermes") / "harvest" / "cff" / "jsonld.json")
    print(data["http://schema.org/name", "jsonld"][0]["@value", "value"])
    print(data["http://schema.org/name", "value"])
    print(data["http://schema.org/author", "jsonld"][0]["@list", "jsonld"][0]["http://schema.org/affiliation", "value"])
    print(data["http://schema.org/author", "value"][-1]["http://schema.org/givenName", "value"])

    access = ValueAccess(data)
    print(access["author"][0]["http://schema.org/givenName"])

    access = JSONLDAccess(data)
    print(access["http://schema.org/author"][0]["@list"][0]["http://schema.org/affiliation"][0]["http://schema.org/name"][0]["@value"])
