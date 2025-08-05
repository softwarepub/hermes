# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from datetime import date, time, datetime

from .ld_container import ld_container
from .ld_list import ld_list
from .ld_dict import ld_dict
from .pyld_util import JsonLdProcessor


_TYPEMAP = [
    # Conversion routines for ld_container
    (
        lambda c: isinstance(c, ld_container),
        {
            "ld_container": lambda c, **_: c,

            "json": lambda c, **_: c.compact(),
            "expanded_json": lambda c, **_: c.ld_value,
        }
    ),

    # Wrap expanded_json to ld_container
    (ld_container.is_ld_id, dict(python=lambda c, **_: c[0]['@id'])),
    (ld_container.is_typed_ld_value, dict(python=ld_container.typed_ld_to_py)),
    (ld_container.is_ld_value, dict(python=lambda c, **_: c[0]['@value'])),
    (ld_list.is_ld_list, dict(ld_container=ld_list)),
    (ld_dict.is_ld_dict, dict(ld_container=ld_dict)),

    # Expand and access JSON data
    (ld_container.is_json_id, dict(python=lambda c: c["@id"], expanded_json=lambda c, **_: [c])),
    (ld_container.is_typed_json_value, dict(python=ld_container.typed_ld_to_py)),
    (ld_container.is_json_value, dict(python=lambda c, **_: c["@value"], expanded_json=lambda c, **_: [c])),
    (ld_list.is_container, dict(ld_container=lambda c, **kw: ld_list([c], **kw))),
    (ld_dict.is_json_dict, dict(ld_container=ld_dict.from_dict)),

    (lambda c: isinstance(c, list), dict(ld_container=ld_list.from_list)),

    # Wrap internal data types
    (lambda v: isinstance(v, (int, float, str, bool)), dict(expanded_json=lambda v, **_: [{"@value": v}])),

    (lambda v: isinstance(v, datetime),
     dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": ["https://schema.org/DateTime"]}])),
    (lambda v: isinstance(v, date),
     dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": ["https://schema.org/Date"]}])),
    (lambda v: isinstance(v, time),
     dict(expanded_json=lambda v, **_: [{"@value": v.isoformat(), "@type": ["https://schema.org/Time"]}])),
]


def init_typemap():
    for typecheck, conversions in _TYPEMAP:
        JsonLdProcessor.register_typemap(typecheck, **conversions)


init_typemap()
