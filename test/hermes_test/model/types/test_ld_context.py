# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from hermes.model.types.ld_context import (
    ContextPrefix,
    ALL_CONTEXTS,
    CODEMETA_CONTEXT,
    PROV_CONTEXT,
)


@pytest.fixture
def ctx():
    return ContextPrefix(ALL_CONTEXTS)


def test_codemeta_prefix(ctx):
    """Default vocabulary in context has the correct base IRI."""
    assert ctx.prefix[None] == "https://codemeta.github.io/terms/"


def test_get_codemeta_item(ctx):
    """Context returns fully expanded terms for default vocabulary in the context."""
    item = ctx["maintainer"]
    assert item == "https://codemeta.github.io/terms/maintainer"


def test_get_prefixed_items(ctx):
    """Context returns fully expanded terms for prefixed vocabularies in the context."""
    item = ctx["schema:Organization"]
    assert item == "http://schema.org/Organization"
    item = ctx["hermes:semanticVersion"]
    assert (
        item
        == "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion"
    )  # TODO: Change on #393 fix


@pytest.mark.parametrize(
    "non_str,error_type",
    [(0, TypeError), (None, TypeError), ([], ValueError), ({"foo"}, ValueError)],
)
def test_get_non_str_item_fail(ctx, non_str, error_type):
    """Context raises on unacceptable input."""
    with pytest.raises(error_type):
        ctx[non_str]


@pytest.mark.parametrize(
    "item",
    [
        "",
        "fooBar",
        [0, "foo"],
        (0, "foo"),
        {"foo": "bar", "baz": "foo"},
        "schema:fooBar",
        "hermes:fooBar",
        "codemeta:maintainer"  # Prefixed CodeMeta doesn't exist in context
    ],
)
def test_get_item_validate_fail(ctx, item):
    """Context raises on terms that don't exist in the context."""
    with pytest.raises(Exception):  # FIXME: Replace with custom error, e.g., hermes.model.errors.InvalidTermException
        ctx[item]
