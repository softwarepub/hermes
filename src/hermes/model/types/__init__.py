# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from .ld_container import ld_container
from .ld_dict import ld_dict
from .ld_list import ld_list
from .pyld_util import JsonLdProcessor


_TYPEMAP = [
    # Conversion routine for ld_container
    (lambda c: isinstance(c, ld_container), {"ld_container": lambda c, **_: c}),

    # Wrap item from ld_dict in ld_list
    (ld_list.is_ld_list, {"ld_container": ld_list}),
    (lambda c: isinstance(c, list), {"ld_container": ld_list}),

    # pythonize items from lists (expanded set is already handled above)
    (ld_container.is_json_id, {"python": lambda c, **_: c["@id"]}),
    (ld_container.is_typed_json_value, {"python": lambda c, **kw: ld_container.typed_ld_to_py([c], **kw)}),
    (ld_container.is_json_value, {"python": lambda c, **_: c["@value"]}),
    (ld_list.is_container, {"ld_container": lambda c, **kw: ld_list([c], **kw)}),
    (ld_dict.is_json_dict, {"ld_container": lambda c, **kw: ld_dict([c], **kw)}),
    (lambda v: isinstance(v, str), {"python": lambda v, parent, **_: parent.ld_proc.compact_iri(parent.active_ctx, v)}),
]


def init_typemap():
    for typecheck, conversions in _TYPEMAP:
        JsonLdProcessor.register_typemap(typecheck, **conversions)


init_typemap()
