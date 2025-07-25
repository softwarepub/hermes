import pytest

from hermes.model.types.ld_context import ContextPrefix, ALL_CONTEXTS, CODEMETA_CONTEXT, PROV_CONTEXT

@pytest.fixture
def ctx():
    return ContextPrefix(ALL_CONTEXTS)

def test_get_default_item(ctx):
    item = ctx["maintainer"]
    assert item == "https://codemeta.github.io/terms/maintainer"

def test_get_prefixed_items(ctx):
    item = ctx["schema:Organization"]
    assert item == "http://schema.org/Organization"
    item = ctx["hermes:semanticVersion"]
    assert item == "https://schema.software-metadata.pub/hermes-content/1.0/semanticVersion"  # TODO: Change on #393 fix


@pytest.mark.parametrize("non_str,error_type", [(0, TypeError), (None, TypeError), ([], ValueError), ({"foo"}, ValueError)])
def test_get_non_str_item_fail(ctx, non_str, error_type):
    with pytest.raises(error_type):
        print(ctx[non_str])

@pytest.mark.parametrize("item", ["", "foo", [0, "foo"], (0, "foo"), {"foo": "bar", "baz": "foo"}])
def test_get_item_fail(ctx, item):
    with pytest.raises(Exception) as e:
        item_ = ctx[item]
        print(item, "->", item_)
