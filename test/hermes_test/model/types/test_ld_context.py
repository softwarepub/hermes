# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from hermes.model.types.ld_context import (
    ContextPrefix,
    ALL_CONTEXTS,
)


@pytest.fixture
def ctx():
    return ContextPrefix(ALL_CONTEXTS)


def test_ctx():
    ctx = ContextPrefix(["u1", {"2": "u2"}])
    assert ctx.context[None] == "u1"
    assert ctx.context["2"] == "u2"


@pytest.mark.xfail(raises=AssertionError, reason="Currently, the wrong CodeMeta IRI is used in the implementation: "
                                                 "https://github.com/softwarepub/hermes/issues/419")
def test_codemeta_prefix(ctx):
    """Default vocabulary in context has the correct base IRI."""
    assert ctx.context[None] == "https://codemeta.github.io/terms/"


def test_get_codemeta_item(ctx):
    """Context returns fully expanded terms for default vocabulary in the context."""
    item = ctx["maintainer"]
    assert item == "https://codemeta.github.io/terms/maintainer"


@pytest.mark.parametrize(
    "compacted,expanded",
    [
        ("schema:Organization", "http://schema.org/Organization"),
        (
            "hermes:semanticVersion",
            "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion",  # TODO: Change on #393 fix
        ),
    ],
)
def test_get_prefixed_items(ctx, compacted, expanded):
    """Context returns fully expanded terms for prefixed vocabularies in the context."""
    item = ctx[compacted]
    assert item == expanded


def test_get_protocol_items_pass(ctx):
    item = ctx["https://schema.org/Organisation"]
    assert item == "https://schema.org/Organisation"


def test_get_protocol_items_fail(ctx):
    with pytest.raises(Exception) as e:
        ctx["https://foo.bar/baz"]
    assert "cannot access local variable" not in str(e.value)  # FIXME: Replace with custom error


@pytest.mark.parametrize(
    "compacted,expanded",
    [
        ([None, "maintainer"], "https://codemeta.github.io/terms/maintainer"),
        (["schema", "Organization"], "http://schema.org/Organization"),
        ((None, "maintainer"), "https://codemeta.github.io/terms/maintainer"),
        (("schema", "Organization"), "http://schema.org/Organization"),
    ],
)
def test_get_valid_non_str_items(ctx, compacted, expanded):
    """Context returns fully expanded terms for valid non-string inputs."""
    assert ctx[compacted] == expanded


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
        "codemeta:maintainer",  # Prefixed CodeMeta doesn't exist in context
        # Even a dict with valid terms should fail, as it is unclear what to expect
        {None: "maintainer", "schema": "Organization"},
    ],
)
def test_get_item_validate_fail(ctx, item):
    """Context raises on terms that don't exist in the context."""
    with pytest.raises(
        Exception
    ):  # FIXME: Replace with custom error, e.g., hermes.model.errors.InvalidTermException
        ctx[item]
