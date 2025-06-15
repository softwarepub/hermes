import datetime
import json
import pathlib
from typing import Annotated, Any, Union, List, Dict, Self, ClassVar, Text

from pydantic import BaseModel, Field, ConfigDict
from hermes.model.ld_utils import jsonld
import jsonpath_ng.ext as jsonpath


class JsonLdModel(BaseModel):
    ContextDict: ClassVar[type] = Dict[str, str | Dict[str, str]]
    ContextType: ClassVar[type] = ContextDict | List[ContextDict | str]

    ld_context: ContextType | None = None
    ld_type: ClassVar[Text | None] = None
    ld_id: Text | None = None

    def __init__(self, *args, **kwargs):
        super(JsonLdModel, self).__init__(*args, **kwargs)

    def model_post_init(self, context):
        for field in self.model_fields_set:
            value = getattr(self, field)
#            if isinstance(value, JsonLdModel) and value.ld_context is None:
#                value.ld_context = self.ld_context


class LazyBuilder:
    _lazy_loader: ClassVar[type]
    _lazy_iri: ClassVar[str | None] = ''
    _lazy_cls: ClassVar[type | None] = None

    def __new__(cls, *args, **kwargs):
        if cls._lazy_cls is None:
            cls.load_cls()
        return cls._lazy_cls.__new__(cls._lazy_cls, *args, **kwargs)

    @classmethod
    def load_cls(cls):
        name = cls.__name__
        bases = cls._lazy_loader.get_bases(cls.__bases__)
        dct = {'__module__': cls.__module__}
        cls._lazy_cls = cls._lazy_loader.load_from_schema(cls._lazy_iri, name, bases, dct)


class LazyModel(JsonLdModel):
    def __class_getitem__(cls, item):
        loader, name = item
        base_cls = type(
            name + 'Base',
            (cls.__base__, ),
            {'__module__': cls.__module__}
        )
        bases = (base_cls, LazyBuilder, )
        dct = {
            '__module__': cls.__module__ + '._lazy',
            '_lazy_loader': loader,
            '_lazy_iri': loader.get_iri(name),
        }
        return type(name, bases, dct)


class _JsonSchemaMetaclass(type(BaseModel)):
    __schema_prefix__ = None

    __stack__ = []
    __schema__ = {}
    __context__ = {}

    __base_class__ = JsonLdModel
    __classes__ = {}
    __builtins__ = {}

    __iri_exp_map__ = {}
    __iri_red_map__ = {}

    @classmethod
    def get_bases(cls, bases):
        return (
            cls.__base_class__, *(
                base for base in bases
                if base is not LazyBuilder
                   and base is not cls.__base_class__
            )
        )

    def __class_getitem__(cls, item):
        prefix, schema_file = item
        schema_path = pathlib.Path(__file__).parent / 'schemas' / schema_file

        schema = json.load(schema_path.open('rb'))
        schema_exp = jsonld.expand(schema)

        dct = {
            '__module__': cls.__module__,
            '__schema__': schema_exp,
            '__schema_prefix__': prefix,
            '__context__': schema['@context'],
        }

        return type(f'_JsonSchemaMetaclass[{prefix}]', (cls, ), dct)

    @classmethod
    def expand_id(cls, context_id):
        if context_id not in cls.__iri_exp_map__:
            doc = {'@context': cls.__context__, context_id: ""}
            exp_doc = jsonld.expand(doc)
            full_id, *_ = exp_doc[0].keys()
            cls.__iri_exp_map__[context_id] = full_id
        return cls.__iri_exp_map__[context_id]

    @classmethod
    def get_iri(cls, name):
        return cls.expand_id(f'{cls.__schema_prefix__}:{name}')

    @classmethod
    def reduce_id(cls, context_id):
        if context_id not in cls.__iri_red_map__:
            doc = [{context_id: [{'@value': ''}]}]
            red_doc = jsonld.compact(doc, cls.__context__)
            red_doc.pop('@context')
            red_id, *_ = red_doc.keys()
            cls.__iri_red_map__[context_id] = red_id
        else:
            red_id = cls.__iri_red_map__[context_id]

        *_, red_name = red_id.split(':', 1)
        return red_name

    def __new__(cls, name, bases, dct, abstract=False):
        if abstract:
            abc_id = f'({name})'
            if abc_id not in cls.__classes__:
                ab_class = super(_JsonSchemaMetaclass, cls).__new__(cls, name, bases, dct)
                cls.__classes__[abc_id] = ab_class
            return cls.__classes__[abc_id]

        schema_id = cls.get_iri(name)
        return cls.load_from_schema(schema_id, name, bases, dct)

    @classmethod
    def find_type(cls, dom_id):
        if dom_id in cls.__builtins__:
            return cls.__builtins__[dom_id]
        elif dom_id in cls.__classes__:
            return cls.__classes__[dom_id]
        else:
            return LazyModel[cls, cls.reduce_id(dom_id)]

    @classmethod
    def _get_value(cls, node, context_id):
        context_id = cls.expand_id(context_id)
        return node[context_id][0]['@value']

    @classmethod
    def load_from_schema(cls, schema_id, name, bases, dct, lazy=False):
        curr_cls = cls.__classes__.get(schema_id, None)
        if curr_cls is None:
            curr_cls = LazyModel[cls, name]
            cls.__classes__[schema_id] = curr_cls
        elif isinstance(curr_cls, _JsonSchemaMetaclass) or lazy:
            return curr_cls

        cls.__stack__.append(schema_id)

        node = cls.find_class(name)

        parents = node.get(cls.expand_id('rdfs:subClassOf'), [])
        if parents:
            bases = tuple(
                cls.load_from_schema(
                    parent['@id'], cls.reduce_id(parent['@id']), bases,
                    {'__module__': dct.get('__module__', cls.__module__)})
                for parent in parents
            )

        props = cls.find_props(node['@id'])
        fields = {}
        for prop in props:
            field_name = cls._get_value(prop, 'rdfs:label')
            field_types = [None]
            for dom in prop[cls.expand_id('schema:rangeIncludes')]:
                dom_id = dom['@id']
                field_types.append(cls.find_type(dom_id))

            field_doc = cls._get_value(prop, 'rdfs:comment')

            fields[field_name] = Annotated[
                Union[*field_types],
                Field(None, title=name, description=field_doc)
            ]

        config = ConfigDict(title=cls._get_value(node, 'rdfs:label'))
        new_cls = super(_JsonSchemaMetaclass, cls).__new__(cls, name, bases, {
            '__doc__': cls._get_value(node, 'rdfs:comment'),
            'model_config': config,
            '__annotations__': fields,
            'ld_type': cls.reduce_id(schema_id),
            **dct
        })

        curr_cls._lazy_cls = new_cls
        cls.__classes__[schema_id] = new_cls

        cls.__stack__.pop()
        return cls.__classes__[schema_id]

    @classmethod
    def find_class(cls, name):
        _item_path = jsonpath.parse(
            f'$[?"@type"[0] = "{cls.expand_id("rdfs:Class")}" & '
            f'"{cls.expand_id("rdfs:label")}"[0]."@value" = "{name}"]'
        )

        _all_nodes = _item_path.find(cls.__schema__)

        if len(_all_nodes) != 1:
            raise ValueError(_item_path)
        else:
            return _all_nodes[0].value

    @classmethod
    def find_props(cls, node_id):
        _props_path = jsonpath.parse(
            f'$[?"@type"[0] = "{cls.expand_id("rdf:Property")}" & '
            f'"{cls.expand_id("schema:domainIncludes")}"[*]."@id" = "{node_id}"]'
        )
        _all_props = _props_path.find(cls.__schema__)

        return [prop.value for prop in _all_props]


class _SchemaOrgMetaclass(_JsonSchemaMetaclass['schema', 'schemaorg-current-https.jsonld']):
    __builtins__ = {
            'https://schema.org/Boolean': bool,
            'https://schema.org/Date': datetime.date,
            'https://schema.org/Float': float,
            'https://schmea.org/Integer': int,
            'https://schema.org/Number': int | float,
            'https://schema.org/Text': Text,
            'https://schema.org/Time': datetime.time,
            'https://schema.org/DateTime': datetime.datetime,
            'https://schema.org/CssSelectorType': Text,
            'https://schema.org/PronounceableText': Text,
            'https://schema.org/URL': Text,
            'https://schema.org/XPathType': Text,
        }


class SchemaOrg(JsonLdModel, metaclass=_SchemaOrgMetaclass, abstract=True):
    pass


_JsonSchemaMetaclass.__base_class__ = SchemaOrg


class _CodemetaMeta(_SchemaOrgMetaclass):
    __context__ = [
        'https://doi.org/10.5063/schema/codemeta-2.0/',
        _SchemaOrgMetaclass.__context__
    ]


class Codemeta(JsonLdModel, metaclass=_CodemetaMeta, abstract=True):
    pass


_CodemetaMeta.__base_class__ = Codemeta


class Person(Codemeta):
    pass


class Organization(Codemeta):
    pass


class SoftwareSourceCode(Codemeta):
    pass


class SoftwareApplication(Codemeta):
    pass


# class _SchemaOrgMetaclass(type(BaseModel)):
#     __stack__ = []
#     __schemas__ = {}
#
#     __classes__ = {}
#
#     def __new__(cls, name, base, dct, abstract=False):
#         if abstract:
#             return super(_SchemaOrgMetaclass, cls).__new__(cls, name, base, dct)
#
#         schema_id = f'https://schema.org/{name}'
#         return cls.load_schema(schema_id, base, dct)
#
#     @classmethod
#     def load_schema(cls, schema_id, base, dct):
#         if schema_id in cls.__classes__:
#             loaded_cls = cls.__classes__[schema_id]
#             if isinstance(loaded_cls, cls):
#                 return loaded_cls
#         else:
#             cls.__classes__[schema_id] = SchemaOrg[schema_id]
#
#         cls.__stack__.append(schema_id)
#         schema_base, name = schema_id.rsplit('/', 1)
#         if schema_id not in cls.__schemas__:
#             cls.__schemas__[schema_id] = schemaorg.Schema(name)
#         schema = cls.__schemas__[schema_id]
#
#         if schema.subTypeOf:
#             base = (cls.load_schema(schema.subTypeOf, base, {}), )
#
#         fields = cls.model_fields(schema._properties.items())
#         dct['model_config'] = cls.model_config(name, schema)
#         dct['__annotations__'] = fields
#         dct['__doc__'] = schema.comment
#
#         new_cls = super(_SchemaOrgMetaclass, cls).__new__(cls, name, base, dct)
#         cls.__classes__[schema_id].__inner_class__ = new_cls
#         cls.__classes__[schema_id] = new_cls
#         cls.__stack__.pop()
#
#         return new_cls
#
#     @classmethod
#     def scan_deps(cls, schema):
#         deps = []
#
#         if schema.subTypeOf:
#             deps.append(schema.subTypeOf)
#
#         for prop_name, prop in schema._properties.items():
#             prop_deps = [dep.strip() for dep in prop['rangeIncludes'].split(',')]
#             deps.extend(
#                 new_dep
#                 for new_dep in prop_deps
#                 if new_dep not in deps
#             )
#
#         order = []
#         for dep in deps:
#             if dep in cls.__schemas__:
#                 continue
#
#             _, dep_name = dep.rsplit('/', 1)
#             cls.__schemas__[dep] = schemaorg.Schema(dep_name)
#
#             order.extend([
#                 new_dep
#                 for new_dep in cls.scan_deps(cls.__schemas__[dep])
#                 if new_dep not in order
#             ] + [dep])
#
#         return order
#
#     @classmethod
#     def model_config(cls, name, schema):
#         return ConfigDict(
#             title=name,
#             json_schema_extra={
#                 '$id': schema.id,
#                 '$schema': schema.base,
#                 'version': float(schema.version)
#             }
#         )
#
#     @classmethod
#     def model_fields(cls, properties):
#         return {
#             name: cls.annotated_field(name, field)
#             for name, field in properties
#         }
#
#     @classmethod
#     def annotated_field(cls, name, properties):
#         field_type = cls.field_type(name, properties['rangeIncludes'])
#         field = Field(
#             None,
#             title=properties['label'],
#             description=properties['comment'],
#         )
#         return Annotated[field_type | List[field_type], field, WithJsonSchema({'$id': properties['id']})]
#
#     @classmethod
#     def field_type(cls, name, ref):
#         type_list = []
#         for iri in ref.split(','):
#             iri = iri.strip()
#             if iri == cls.__stack__[-1]:
#                 res = Self
#             elif iri in cls.__builtins__:
#                 res = cls.__builtins__[iri]
#             else:
#                 if not iri in cls.__classes__:
#                     cls.__classes__[iri] = SchemaOrg[iri]
#                 res = cls.__classes__.get(iri, None)
#             type_list.append(res or Any)
#
#         if len(type_list) == 0:
#             return Any
#         else:
#             return Union[None, *type_list]
#
#
#
#
# class JsonLd(BaseModel):
#     ContextDict: ClassVar[type] = Dict[str, str | Dict[str, str]]
#     ContextType: ClassVar[type] = ContextDict | List[ContextDict | str]
#
#     jsonld_iri: ClassVar[str]
#     jsonld_context: ContextType = None
#
#     def model_validate(
#         cls,
#         obj: Any,
#         *,
#         strict: bool | None = None,
#         from_attributes: bool | None = None,
#         context: Any | None = None,
#     ) -> Self:
#         return obj
#
#
# class SchemaOrg(JsonLd):
#     jsonld_context: JsonLd.ContextType = ['https://schema.org']
#     jsonld_class: ClassVar[type | None] = None
#
#     class LazyBuilder:
#         def __new__(cls, *args, **kwargs):
#             if cls.jsonld_class is None:
#                 bases = tuple(base for base in cls.__bases__ if not base is SchemaOrg.LazyBuilder)
#                 cls.jsonld_class = _SchemaOrgMetaclass.load_schema(cls.jsonld_iri, bases, {})
#             return cls.jsonld_class.__new__(cls.jsonld_class, *args, **kwargs)
#
#     def __class_getitem__(cls, iri):
#         _, name = iri.rsplit('/', 1)
#         base_class = type(
#             f'{name}Base',
#             (cls, ),
#             {'jsonld_iri': iri}
#         )
#         return type(name, (base_class, cls.LazyBuilder), {'jsonld_class': None})
#
#
# class SchemaOrgType(SchemaOrg, metaclass=_SchemaOrgMetaclass, abstract=True):
#     pass
#
#
