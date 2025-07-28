# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>


CODEMETA_PREFIX = "https://doi.org/10.5063/schema/codemeta-2.0"
CODEMETA_CONTEXT = [CODEMETA_PREFIX]

SCHEMA_ORG_PREFIX = "http://schema.org/"
SCHEMA_ORG_CONTEXT = [{"schema": SCHEMA_ORG_PREFIX}]

PROV_PREFIX = "http://www.w3.org/ns/prov#"
PROV_CONTEXT = [{"prov": PROV_PREFIX}]

HERMES_RT_PREFIX = 'https://schema.software-metadata.pub/hermes-runtime/1.0/'
HERMES_RT_CONTEXT = [{'hermes-rt': HERMES_RT_PREFIX}]
HERMES_CONTENT_CONTEXT = [{'hermes': 'https://schema.software-metadata.pub/hermes-content/1.0/'}]

HERMES_CONTEXT = [{**HERMES_RT_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]}]

HERMES_BASE_CONTEXT = [*CODEMETA_CONTEXT, {**SCHEMA_ORG_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]}]
HERMES_PROV_CONTEXT = [{**SCHEMA_ORG_CONTEXT[0], **HERMES_RT_CONTEXT[0], **PROV_CONTEXT[0]}]

ALL_CONTEXTS = [*CODEMETA_CONTEXT, {**SCHEMA_ORG_CONTEXT[0], **PROV_CONTEXT[0], **HERMES_CONTEXT[0]}]


class ContextPrefix:
    """
    FIXME: Rename to `LDContext`, `HermesLDContext` or similar,
    FIXME: as this class represents JSON-LD contexts.
    Represents the context of the hermes JSON-LD data model and provides two views on the model:

    - as a two-item list, of which the first item is the default, unprefixed vocabulary IRI, and the second is a dict
    mapping prefixes to vocabulary IRIs;
    - as a dict mapping prefixes to vocabulary IRIs, where the default vocabulary has a prefix of None.
    """
    def __init__(self, context):
        """
        @param context: A two-item list, where the first item is the default vocabulary's IRI string, and the second
        is a dict mapping vocabulary prefixes to their respective IRI string.

        # FIXME: Rename context and prefix to context_lst (or similar) and context respectively,
        # FIXME: as currently, prefix represents the actual context more precisely than the throwaway value of context.
        """
        self.context = context
        self.prefix = {}

        for ctx in self.context:
            if isinstance(ctx, str):
                ctx = {None: ctx}

            self.prefix.update({
                prefix: base_url
                for prefix, base_url in ctx.items()
                if isinstance(base_url, str)
            })


    def __getitem__(self, item):
        """
        FIXME: Document in class, not here
        FIXME: Add type hints for params and return

        Gets the fully qualified IRI for a term from a vocabulary inside the initialized context.
        The vocabulary must have been added to the context at initialization.

        @param item: A term from a vocabulary in the context; terms from the default vocabulary are passed with a prefix
        of None, or as an unprefixed string, terms from non-default vocabularies are prefixed with the defined prefix
        for the vocabulary. The term can either be passed in as string <term> if prefix is None, or "prefix:term", or
        as a two-element list ["prefix": "term"] or tuple ("prefix", "term")
        @return: The fully qualified IRI for the passed term
        """
        if not isinstance(item, str):  # FIXME: Rename to compressed_term
            prefix, name = item  # FIXME: "name" should be "term", "prefix" should be "base_iri"
        elif ':' in item:
            prefix, name = item.split(':', 1)
            if name.startswith('://'):
                prefix, name = True, item
        else:
            prefix, name = None, item

        if prefix in self.prefix:
            item = self.prefix[prefix] + name  # FIXME: Rename "item" to "iri"

        return item


iri_map = ContextPrefix(ALL_CONTEXTS)
