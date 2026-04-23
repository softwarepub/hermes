# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
# SPDX-FileContributor: Michael Fritzsche

from typing import Union
from typing_extensions import Self

from hermes.model.error import HermesContextError


CODEMETA_PREFIX: str = "https://doi.org/10.5063/schema/codemeta-2.0"
""" The prefix for codemeta terms. """
CODEMETA_CONTEXT: list[str] = [CODEMETA_PREFIX]
""" The prefix for codemeta terms wrapped inside a list. """

SCHEMA_ORG_PREFIX: str = "http://schema.org/"
""" The prefix for schema.org terms. """
SCHEMA_ORG_CONTEXT: list[dict[str, str]] = [{"schema": SCHEMA_ORG_PREFIX}]
""" The prefix for schema.org terms as value of the shortend prefix schema in a dict inside of a list. """

PROV_PREFIX: str = "http://www.w3.org/ns/prov#"
""" The prefix for provenance terms. """
PROV_CONTEXT: list[dict[str, str]] = [{"prov": PROV_PREFIX}]
""" The prefix for provenance terms as value of the shortend prefix schema in a dict inside of a list. """

HERMES_RT_PREFIX: str = "https://schema.software-metadata.pub/hermes-runtime/1.0/"
""" The prefix for HERMES runtime terms. """
HERMES_RT_CONTEXT: list[dict[str, str]] = [{"hermes-rt": HERMES_RT_PREFIX}]
""" The prefix for HERMES runtime terms as value of the shortend prefix schema in a dict inside of a list. """
HERMES_CONTENT_CONTEXT: list[dict[str, str]] = [
    {"hermes": "https://schema.software-metadata.pub/hermes-content/1.0/"}
]
""" The prefix for HERMES content terms as value of the shortend prefix schema in a dict inside of a list. """

HERMES_CONTEXT: list[dict[str, str]] = [{**HERMES_RT_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]}]
""" A list containing a dict containing all key, value pairs from HERMES_RT_CONTEXT and HERMES_CONTENT_CONTEXT. """

HERMES_BASE_CONTEXT: list[dict[str, str]] = [
    *CODEMETA_CONTEXT,
    {**SCHEMA_ORG_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]},
]
""" The JSON_LD context commonly used by HERMES excluding provenance context. """
HERMES_PROV_CONTEXT: list[dict[str, str]] = [
    {**SCHEMA_ORG_CONTEXT[0], **HERMES_RT_CONTEXT[0], **PROV_CONTEXT[0]}
]
""" The JSON_LD context commonly used by HERMES excluding codemeta context. """

ALL_CONTEXTS: list[Union[str, dict[str, str]]] = [
    *CODEMETA_CONTEXT,
    {**SCHEMA_ORG_CONTEXT[0], **PROV_CONTEXT[0], **HERMES_CONTEXT[0]},
]
""" list[str | dict[str, str]]: The JSON_LD context commonly used by HERMES. """


class ContextPrefix:
    """
    FIXME: Rename to `LDContext`, `HermesLDContext` or similar, as this class represents JSON-LD contexts.
    Represents the context of the hermes JSON-LD data model and provides two views on the model:

    - as a list of linked data vocabularies, where items can be vocabulary base IRI strings and/or dictionaries mapping
        arbitrary strings used to prefix terms from a specific vocabulary to their respective vocabulary IRI strings.;
    - as a dict mapping prefixes to vocabulary IRIs, where the default vocabulary has a prefix of None.

    Attributes:
        vocabularies (list[str | dict]): The list of JSON_LD context used for expansion.
        context dict[str | None, str]: The mapping of prefix its expanded IRI.
    """

    def __init__(self: Self, vocabularies: list[Union[str, dict]]) -> None:
        """
        If the list contains more than one string item, the last one will be used as the default vocabulary. If a prefix
        string is used more than once across all dictionaries in the list, the last item with this key will be included
        in the context.

        Args:
            vocabularies (list[str | dict]): A list of linked data vocabularies. Items can be vocabulary base IRI
                strings and/or dictionaries mapping arbitrary strings used to prefix terms from a specific vocabulary to
                their respective vocabulary IRI strings.

        Returns:
            None:
        """
        self.vocabularies = vocabularies
        self.context = {}

        # add every entry in the vocabulary to the context
        for vocab in self.vocabularies:
            if isinstance(vocab, str):
                vocab = {None: vocab}

            # add all prefix, base_iri pairs from vocab to context
            self.context.update(
                {
                    prefix: base_iri
                    for prefix, base_iri in vocab.items()
                    if isinstance(base_iri, str)
                }
            )

    def __getitem__(self: Self, compressed_term: Union[str, tuple]) -> str:
        """
        Gets the fully qualified IRI for a term from a vocabulary inside the initialized context.
        The vocabulary must have been added to the context at initialization.

        Example uses:

            context = <self>(["iri_default", {"prefix1": "iri1"}])\n
            # access qualified term via str\n
            term = context["term_in_default_vocabulary"]\n
            term = context["prefix1:term"]\n
            # access qualified term via tuple\n
            term = context["prefix1", "term"]\n
            term = context[None, "term_in_default_vocabulary"]

        Args:
            compressed_term (str | tuple): A term from a vocabulary in the context; terms from the default vocabulary
                are passed with a prefix of None, or as an unprefixed string, terms from non-default vocabularies are
                prefixed with the defined prefix for the vocabulary. The term can either be passed in as string <term>
                if prefix is None, or "<prefix>:<term>", or as a tuple.

        Returns:
            str: The fully qualified IRI for the passed term

        Raises:
            HermesContextError: If the compressed term is '' or its prefix can't be expanded.
        """
        # seperate the prefix from the term
        if not isinstance(compressed_term, str):
            prefix, term = compressed_term
        elif ":" in compressed_term:
            prefix, term = compressed_term.split(":", 1)
            if term.startswith("://"):
                prefix, term = True, compressed_term
        elif compressed_term != "":
            prefix, term = None, compressed_term
        else:
            raise HermesContextError(compressed_term)

        # expand the prefix
        try:
            base_iri = self.context[prefix]
        except KeyError as ke:
            raise HermesContextError(prefix) from ke

        # return the expanded term
        return base_iri + term


iri_map: ContextPrefix = ContextPrefix(ALL_CONTEXTS)
""" An object returning the fully qualified IRI for a compressed term using the contexts in ALL_CONTEXTS. """
