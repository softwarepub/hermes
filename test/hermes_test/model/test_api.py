import pytest

from hermes.model import SoftwareMetadata

from hermes.model.types.ld_context import ALL_CONTEXTS

EXTRA_VOCABS = {"foo": "https://bar.net/schema"}


@pytest.fixture
def default_context():
    return {"@context": ALL_CONTEXTS}

@pytest.fixture
def custom_context():
    return {"@context": ALL_CONTEXTS + [EXTRA_VOCABS]}


@pytest.mark.parametrize("metadata,full_context", [
    (SoftwareMetadata(), "default_context"),
    (SoftwareMetadata(extra_vocabs=EXTRA_VOCABS), "custom_context"),
])
def test_init_no_data(metadata, full_context, request):
    assert metadata.full_context == request.getfixturevalue(full_context)["@context"]


@pytest.mark.parametrize("metadata,full_context", [
    (SoftwareMetadata({"funding": "foo"}), "default_context"),
    (SoftwareMetadata({"funding": "foo"}, extra_vocabs=EXTRA_VOCABS), "custom_context"),
])
def test_init_with_data(metadata, full_context, request):
    assert metadata.full_context == request.getfixturevalue(full_context)["@context"]
    assert metadata["funding"] == "foo"


def test_init_full_object():
    my_software = {"foo:softwareName": "MySoftware", "foo:egg": "spam", "foo:ham": "eggs",
                   "maintainer": {"name": "Some Name", "email": "maintainer@example.com"},
                   "author": [{"name": "Foo"}, {"name": "Bar"}]}
    data = SoftwareMetadata(my_software, extra_vocabs={"foo": "https://foo.bar"})
    assert data["foo:softwareName"] == "MySoftware"
    assert data["maintainer"]["name"] == "Some Name"
    for author in data["author"]:
        assert author["name"] in ["Foo", "Bar"]
