# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from datetime import date, time, datetime

from .ld_container import ld_container
from .ld_list import ld_list
from .ld_dict import ld_dict
from .ld_context import iri_map
from .pyld_util import JsonLdProcessor


_TYPEMAP = [
    # Conversion routines for ld_container
    (
        lambda c: isinstance(c, ld_container),
        {
            "ld_container": lambda c, **_: c,
            "json": lambda c, **_: c.compact(),
            "expanded_json": lambda c, **_: c.ld_value,
        },
    ),

    # Wrap item from ld_dict in ld_list
    (ld_list.is_ld_list, dict(ld_container=ld_list)),
    (
     lambda c: isinstance(c, list) and all(isinstance(item, dict) for item in c),
     dict(ld_container=lambda c, **kw: ld_list([{"@list": c}], **kw))
    ),

    # pythonize items from lists (expanded set is already handled above)
    (ld_container.is_json_id, dict(python=lambda c, **_: c["@id"])),
    (ld_container.is_typed_json_value, dict(python=ld_container.typed_ld_to_py)),
    (ld_container.is_json_value, dict(python=lambda c, **_: c["@value"])),
    (ld_list.is_container, dict(ld_container=lambda c, **kw: ld_list([c], **kw))),
    (ld_dict.is_json_dict, dict(ld_container=lambda c, **kw: ld_dict([c], **kw))),

    # Convert internal data types to expanded_json
    (lambda c: ld_container.is_json_id(c) or ld_container.is_json_value(c), dict(expanded_json=lambda c, **_: [c])),
    (ld_dict.is_json_dict, dict(expanded_json=lambda c, **kw: ld_dict.from_dict(c, **kw).ld_value)),
    (ld_dict.is_ld_dict, dict(expanded_json=lambda c, **kw: ld_dict.from_dict(c[0], **kw).ld_value)),
    (
        ld_list.is_container,
        dict(
            expanded_json=lambda c, **kw: ld_list.from_list(
                ld_list([c]).item_list, container=ld_list([c]).container, **kw
            ).ld_value
        ),
    ),
    (
        ld_list.is_ld_list,
        dict(
            expanded_json=lambda c, **kw: ld_list.from_list(
                ld_list(c).item_list, container=ld_list(c).container, **kw
            ).ld_value
        ),
    ),
    (lambda c: isinstance(c, list), dict(expanded_json=lambda c, **kw: ld_list.from_list(c, **kw).ld_value)),
    (lambda v: isinstance(v, (int, float, str, bool)), dict(expanded_json=lambda v, **_: [{"@value": v}])),
    (
        lambda v: isinstance(v, datetime),
        dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:DateTime"]}]),
    ),
    (
        lambda v: isinstance(v, date),
        dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:Date"]}]),
    ),
    (
        lambda v: isinstance(v, time),
        dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:Time"]}]),
    ),
]


def init_typemap():
    for typecheck, conversions in _TYPEMAP:
        JsonLdProcessor.register_typemap(typecheck, **conversions)


init_typemap()
