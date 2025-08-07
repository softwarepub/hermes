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


@pytest.mark.xfail(
    raises=AssertionError,
    reason="Currently, the wrong CodeMeta IRI is used in the implementation: "
    "https://github.com/softwarepub/hermes/issues/419",
)
def test_codemeta_prefix(ctx):
    """Default vocabulary in context has the correct base IRI."""
    assert ctx.context[None] == "https://codemeta.github.io/terms/"


@pytest.mark.xfail(
    raises=AssertionError,
    reason="Currently, the wrong CodeMeta IRI is used in the implementation, so expanding terms doesn't work correctly, "
    "see https://github.com/softwarepub/hermes/issues/419",
)
@pytest.mark.parametrize("compacted", ["maintainer", (None, "maintainer")])
def test_get_item_from_default_vocabulary_pass(ctx, compacted):
    """Context returns fully expanded terms for default vocabulary in the context."""
    item = ctx[compacted]
    assert item == "https://codemeta.github.io/terms/maintainer"


@pytest.mark.parametrize(
    "compacted,expanded",
    [
        ("schema:Organization", "http://schema.org/Organization"),
        (
            "hermes:semanticVersion",
            "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion",  # TODO: Change on #393 fix
        ),
        (("schema", "Organization"), "http://schema.org/Organization"),
        (
            ("hermes", "semanticVersion"),
            "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion",
        ),  # TODO: Change on #393 fix
    ],
)
def test_get_item_from_prefixed_vocabulary_pass(ctx, compacted, expanded):
    """
    Context returns fully expanded terms for prefixed vocabularies in the context,
    for all accepted parameter formats.
    """
    item = ctx[compacted]
    assert item == expanded


@pytest.mark.parametrize(
    "not_exist",
    [
        "foobar:baz",
        ("foobar", "baz"),
    ],
)
def test_get_item_from_prefixed_vocabulary_raises_on_prefix_not_exist(ctx, not_exist):
    """
    Tests that an exception is raised when trying to get compacted items for which there is no
    prefixed vocabulary in the context, and that the raised exception is not raised due to side effects.
    """
    with pytest.raises(Exception) as e:  # FIXME: Replace with custom error
        ctx[not_exist]
    if any(
        s in str(e.value)
        for s in ["cannot access local variable", "referenced before assignment"]
    ):
        pytest.fail(f"Unexpected exception raised not due to the expected cause: {e.value}.")


@pytest.mark.parametrize(
    "not_exist",
    [
        "baz",
        "hermes:baz",
        "schema:baz",
        (None, "baz"),
        ("hermes", "baz"),
        ("schema", "baz"),
    ],
)
def test_get_item_from_prefixed_vocabulary_raises_on_term_not_exist(ctx, not_exist):
    """
    Tests that an exception is raised when trying to get compacted items for which the vocabulary exists,
    but doesn't contain the requested term, and that the raised exception is not raised due to side effects.
    """
    with pytest.raises(Exception) as e:  # FIXME: Replace with custom error
        ctx[not_exist]
    if any(
        s in str(e.value)
        for s in ["cannot access local variable", "referenced before assignment"]
    ):
        pytest.fail(f"Unexpected exception raised not due to the expected cause: {e.value}.")


@pytest.mark.parametrize(
    "expanded",
    [
        "https://codemeta.github.io/terms/maintainer",
        "https://schema.org/Organisation",
        "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion",
    ],
)
@pytest.mark.xfail(
    raises=NotImplementedError,
    reason="Passing back expanded terms on their input if they are valid in the context "
           "is not yet implemented (or decided).",
)
def test_get_item_from_expanded_pass(ctx, expanded):
    """
    Tests that getting items via their fully expanded terms works as expected.
    """
    with pytest.raises(Exception) as e:
        assert ctx[expanded] == expanded
    raise NotImplementedError


def test_get_item_from_expanded_fail(ctx):
    """
    Tests that context raises on unsupported expanded term input.
    """
    with pytest.raises(Exception) as e:
        ctx["https://foo.bar/baz"]
    if any(
        s in str(e.value)
        for s in ["cannot access local variable", "referenced before assignment"]
    ):
        pytest.fail(f"Unexpected exception raised not due to the expected cause: {e.value}.")


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
