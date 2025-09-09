import pytest

from hermes.model import SoftwareMetadata

from hermes.model.types.ld_context import ALL_CONTEXTS

EXTRA_VOCABS = {"foo": "https://bar.net/schema"}

@pytest.fixture
def default_context():
    return {"@context": ALL_CONTEXTS}

@pytest.fixture
def default_ld():
    return {"@context": ALL_CONTEXTS, "funding": "foo"}

@pytest.fixture
def custom_context():
    return {"@context": ALL_CONTEXTS + [EXTRA_VOCABS]}

@pytest.fixture
def custom_ld():
    return {"@context": ALL_CONTEXTS + [EXTRA_VOCABS], "funding": "foo"}

@pytest.fixture
def none():
    return None

@pytest.mark.parametrize("data,codemeta,full_context,expanded", [
    (SoftwareMetadata(), "default_context", "default_context", "none"),  # FIXME: Replace none fixtures
    (SoftwareMetadata({"funding": "foo"}), "default_ld", "none", "none"),  # FIXME: Replace none fixtures
    (SoftwareMetadata(extra_vocabs=EXTRA_VOCABS), "custom_context", "custom_context", "none"),  # FIXME: Replace none fixtures
    (SoftwareMetadata({"funding": "foo"}, extra_vocabs=EXTRA_VOCABS), "custom_ld", "none", "none"),  # FIXME: Replace none fixtures
])
def test_init(data, codemeta, full_context, expanded, request):
    assert data.compact() == request.getfixturevalue(codemeta)
    assert data.full_context == request.getfixturevalue(full_context)["@context"]
    assert data.ld_value == request.getfixturevalue(expanded)

