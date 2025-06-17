# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from hermes.model.types.ld_context import iri_map as iri

from .action import Reject, Replace, Collect, Concat, MergeSet
from .match import match_equals, match_keys


REPLACE_STRATEGY = {
    None: {
        None: Replace,
        "@type": Collect(match_equals),
    },
}


REJECT_STRATEGY = {
    None: {
        None: Reject,
        "@type": Collect(match_equals),
    },
}


PROV_STRATEGY = {
    None: {
        iri["hermes-rt:graph"]: Concat,
        iri["hermes-rt:replace"]: Concat,
        iri["hermes-rt:reject"]: Concat,
    },
}


CODEMETA_STRATEGY = {
    iri["schema:SoftwareSourceCode"]: {
        iri["schema:author"]: MergeSet(match_keys('@id', iri['schema:email'])),
    },
}
