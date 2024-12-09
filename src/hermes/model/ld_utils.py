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
