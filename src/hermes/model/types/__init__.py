# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

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
        }
    ),

    # Wrap item from ld_dict in ld_list
    (ld_list.is_ld_list, {"ld_container": ld_list}),
    (lambda c: isinstance(c, list), {"ld_container": lambda c, **kw: ld_list(c, **kw)}),

    # pythonize items from lists (expanded set is already handled above)
    (ld_container.is_json_id, {"python": lambda c, **_: c["@id"]}),
    (ld_container.is_typed_json_value, {"python": lambda c, **kw: ld_container.typed_ld_to_py([c], **kw)}),
    (ld_container.is_json_value, {"python": lambda c, **_: c["@value"]}),
    (ld_list.is_container, {"ld_container": lambda c, **kw: ld_list([c], **kw)}),
    (ld_dict.is_json_dict, {"ld_container": lambda c, **kw: ld_dict([c], **kw)}),
    (lambda v: isinstance(v, str), {"python": lambda v, parent, **_: parent.ld_proc.compact_iri(parent.active_ctx, v)}),

    # Convert internal data types to expanded_json
    (ld_container.is_json_id, {"expanded_json": lambda c, **_: [c]}),
    (ld_container.is_ld_id, {"expanded_json": lambda c, **_: c}),
    (ld_container.is_json_value, {"expanded_json": lambda c, **_: [c]}),
    (ld_container.is_ld_value, {"expanded_json": lambda c, **_: c}),
    (ld_dict.is_json_dict, {"expanded_json": lambda c, **kw: ld_dict.from_dict(c, **kw).ld_value}),
    (
        ld_list.is_container,
        {"expanded_json": lambda c, **kw: ld_list.from_list(ld_list.get_item_list_from_container(c), **kw).ld_value}
    ),
    (
        ld_list.is_ld_list,
        {"expanded_json": lambda c, **kw: ld_list.from_list(ld_list.get_item_list_from_container(c[0]), **kw).ld_value}
    ),
    (lambda c: isinstance(c, list), {"expanded_json": lambda c, **kw: ld_list.from_list(c, **kw).ld_value}),
    (lambda v: isinstance(v, (int, float, str, bool)), {"expanded_json": lambda v, **_: [{"@value": v}]}),
    (
        lambda v: isinstance(v, datetime),
        {"expanded_json": lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:DateTime"]}]}
    ),
    (
        lambda v: isinstance(v, date),
        {"expanded_json": lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:Date"]}]}
    ),
    (
        lambda v: isinstance(v, time),
        {"expanded_json": lambda v, **_: [{"@value": v.isoformat(), "@type": iri_map["schema:Time"]}]}
    ),
]


def init_typemap():
    for typecheck, conversions in _TYPEMAP:
        JsonLdProcessor.register_typemap(typecheck, **conversions)


init_typemap()
