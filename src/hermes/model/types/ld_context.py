# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0
import typing

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

    - as a list of linked data vocabularies, where items can be vocabulary base IRI strings and/or dictionaries mapping
    arbitrary strings used to prefix terms from a specific vocabulary to their respective vocabulary IRI strings.;
    - as a dict mapping prefixes to vocabulary IRIs, where the default vocabulary has a prefix of None.
    """
    def __init__(self, vocabularies: list[str | dict]):
        """
        @param vocabularies: A list of linked data vocabularies. Items can be vocabulary base IRI strings and/or dictionaries
        mapping arbitrary strings used to prefix terms from a specific vocabulary to their respective vocabulary IRI
        strings.

        If the list contains more than one string item, the last one will be used as the default vocabulary. If a prefix
        string is used more than once across all dictionaries in the list, the last item with this key will be included
        in the context.
        """
        self.vocabularies = vocabularies
        self.context = {}

        for vocab in self.vocabularies:
            if isinstance(vocab, str):
                vocab = {None: vocab}

            self.context.update({
                prefix: base_iri
                for prefix, base_iri in vocab.items()
                if isinstance(base_iri, str)
            })


    def __getitem__(self, compressed_term: str | tuple) -> str:
        """
        Gets the fully qualified IRI for a term from a vocabulary inside the initialized context.
        The vocabulary must have been added to the context at initialization.

        Example uses:

            context = <self>(["iri_default", {"prefix1": "iri1"}])
            # access qualified term via str
            term = context["term_in_default_vocabulary"]
            term = context["prefix1:term"]
            # access qualified term via tuple
            term = context["prefix1", "term"]
            term = context[None, "term_in_default_vocabulary"]

        @param compressed_term: A term from a vocabulary in the context; terms from the default vocabulary are passed
        with a prefix of None, or as an unprefixed string, terms from non-default vocabularies are prefixed with the
        defined prefix for the vocabulary. The term can either be passed in as string <term> if prefix is None, or
        "<prefix>:<term>", or as a tuple.

        @return: The fully qualified IRI for the passed term
        """
        if not isinstance(compressed_term, str):
            prefix, term = compressed_term
        elif ':' in compressed_term:
            prefix, term = compressed_term.split(':', 1)
            if term.startswith('://'):
                prefix, term = True, compressed_term
        else:
            prefix, term = None, compressed_term

        if prefix in self.context:
            iri = self.context[prefix] + term

        return iri


iri_map = ContextPrefix(ALL_CONTEXTS)
