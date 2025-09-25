import pytest

from hermes.model import SoftwareMetadata
from hermes.model.types import ld_list, ld_dict

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


def test_init_nested_object():
    my_software = {"foo:softwareName": "MySoftware", "foo:egg": "spam", "foo:ham": "eggs",
                   "maintainer": {"name": "Some Name", "email": "maintainer@example.com"},
                   "author": [{"name": "Foo"}, {"name": "Bar"}]}
    data = SoftwareMetadata(my_software, extra_vocabs={"foo": "https://foo.bar"})
    assert data["foo:softwareName"] == "MySoftware"
    assert data["maintainer"]["name"] == "Some Name"
    for author in data["author"]:
        assert author["name"] in ["Foo", "Bar"]


def test_add():
    data = SoftwareMetadata()
    data.add("foo", "a")
    assert data["foo"] == "a"
    data.add("foo", "b")
    assert type(data["foo"]) is ld_list and data["foo"].item_list == [{"@value": "a"}, {"@value": "b"}]
    data.add("foo", "c")
    assert data["foo"].item_list == [{"@value": "a"}, {"@value": "b"}, {"@value": "c"}]
    data = SoftwareMetadata()
    # FIXME: #433 will fix this
    data.add("foo", {"bar": "foo"})
    assert type(data["foo"]) is ld_dict and data["foo"].data_dict == {"bar": "foo"}
    data.add("foo", {"bar": "foo"})
    assert type(data["foo"]) is ld_list and data["foo"].item_list == 2 * [{"bar": "foo"}]
    data.add("foo", {"bar": "foo"})
    assert data["foo"].item_list == 3 * [{"bar": "foo"}]


def test_iterative_assignment():
    # This tests iterative assignments/traversals to edit/appending values
    # This requires SoftwareMetadata.__getitem__ to return a plain dict. SoftwareMetadata.__setitem__ can then
    # implement the isinstanceof checks that @notactuallyfinn suggested.
    data = SoftwareMetadata(extra_vocabs={"foo": "https://foo.bar"})
    data["author"] = {"name": "Foo"}
    # Look, a squirrel!
    authors = data["author"]
    assert type(authors) is list
    author1 = authors[0]
    author1["email"] = "author@example.com"
    authors[0] = author1
    assert len(authors) == 1
    authors.append({"name": "Bar", "email": "author2@example.com"})
    data["author"] = authors
