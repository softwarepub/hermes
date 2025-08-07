# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import json
import typing as t
import uuid
from pathlib import Path

import rdflib
from frozendict import frozendict
from pyld import jsonld


class BundledLoader:
    """ Loader that retrieves schemas that come bundled with the software. """

    def __init__(self,
                 schema_path: t.Optional[Path] = None,
                 base_loader: t.Any = None,
                 preload: t.Union[bool, t.List[str], None] = None):
        self.cache = []
        self.schema_path = schema_path or Path(__file__).parent / "schemas"
        self.base_loader = base_loader or jsonld.get_document_loader()
        self.toc = json.load((self.schema_path / 'index.json').open('rb'))

        self.loaders = {
            "json": self._load_json,
            "rdflib": self._load_rdflib,
        }

        if preload is True:
            preload = [t["url"] for t in self.toc]
        elif not preload:
            preload = []

        for url in preload:
            self.load_schema(url)

    def _load_json(self, source, base_url):
        return {
            'contentType': 'application/ld+json',
            'contextUrl': None,
            'documentUrl': base_url,
            'document': json.load(source),
        }

    def _load_rdflib(self, source, base_url):
        graph = rdflib.Graph()
        graph.parse(source, base_url)
        json_ld = json.loads(graph.serialize(format="json-ld"))

        return {
            'contentType': 'application/ld+json',
            'contextUrl': None,
            'documentUrl': base_url,
            'document': {"@graph": json_ld},
        }

    def load_schema(self, url):
        for entry in self.toc:
            if entry['url'] == url:
                break
        else:
            return None

        source = self.schema_path / entry['file']
        load_func = self.loaders[entry.get("loader", "json")]
        cache_entry = load_func(source.open('rb'), url)
        self.cache.append(cache_entry)

        return cache_entry

    def __call__(self, url, options=None):
        for schema in self.cache:
            if url.startswith(schema['documentUrl']):
                return schema

        entry = self.load_schema(url)
        if entry is None:
            return self.base_loader(url, options)
        else:
            return entry


bundled_loader = BundledLoader(preload=True)
jsonld.set_document_loader(bundled_loader)


class JsonLdProcessor(jsonld.JsonLdProcessor):
    """ Custom JsonLdProcessor to get access to the inner functionality. """

    _type_map = {}

    _INITIAL_CONTEXT = frozendict({
        '_uuid': str(uuid.uuid1()),
        'processingMode': 'json-ld-1.1',
        'mappings': {}
    })

    def expand_iri(self, active_ctx: t.Any, short_iri: str) -> str:
        return self._expand_iri(active_ctx, short_iri, vocab=True)

    def compact_iri(self, active_ctx: t.Any, long_iri: str) -> str:
        return self._compact_iri(active_ctx, long_iri, vocab=True)

    def initial_ctx(self, local_ctx, options=None):
        return self.process_context(self._INITIAL_CONTEXT, local_ctx, options or {})

    @classmethod
    def register_typemap(cls, typecheck, **conversions):
        for output, convert_func in conversions.items():
            cls._type_map[output] = cls._type_map.get(output, [])
            cls._type_map[output].append((typecheck, convert_func))

    @classmethod
    def apply_typemap(cls, value, *option, **kwargs):
        for opt in option:
            for check, conv in cls._type_map.get(opt, []):
                if check(value):
                    return conv(value, **kwargs), opt

        return value, None
