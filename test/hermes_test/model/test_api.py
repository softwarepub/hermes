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
    my_software = {
        "foo:softwareName": "MySoftware",
        "foo:egg": "spam",
        "foo:ham": "eggs",
        "maintainer": {"name": "Some Name", "email": "maintainer@example.com"},
        "author": [{"name": "Foo"}, {"name": "Bar"}],
    }
    data = SoftwareMetadata(my_software, extra_vocabs={"foo": "https://foo.bar"})
    assert data["foo:softwareName"] == ["MySoftware"]
    assert data["maintainer"]["name"] == ["Some Name"]
    for author in data["author"]:
        assert author["name"] in [["Foo"], ["Bar"]]


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
    assert isinstance(authors, list)
    author1 = authors[0]
    author1["email"] = "author@example.com"
    authors[0] = author1
    authors.append({"name": "Bar", "email": "author2@example.com"})
    data["author"] = authors
    assert len(authors) == 2


def test_usage():
    data = SoftwareMetadata()
    data["author"] = {"name": "Foo"}
    data["author"].append({"name": "Bar"})
    data["author"][0]["email"] = "foo@bar.net"
    data["author"][0]["email"].append("foo@baz.com")
    assert len(data["author"]) == 2
    assert len(data["author"][1]["email"]) == 2
    assert len(data["author"][0]["email"]) == 0
    harvest = {
        "authors": [
            {"name": "Foo", "affiliations": ["Uni A", "Lab B"], "kw": ["a", "b", "c"]},
            {"name": "Bar", "affiliations": ["Uni C"], "email": "bar@c.edu"},
            {"name": "Baz", "affiliations": ["Lab E"]},
        ]
    }
    for author in harvest["authors"]:
        for exist_author in data["author"]:
            if author["name"] == exist_author["name"]:
                exist_author["affiliation"] = author["affiliations"]
                exist_author["email"].append(author["email"])
                exist_author["schema:knowsAbout"].append(kw for kw in author["kw"])
    assert len(data["author"]) == 3
    foo, bar, baz = data["author"]
    assert foo["name"] == "Foo"
    assert foo["affiliation"] == ["Uni A", "Lab B"]
    assert foo["schema:knowsAbout"] == ["a", "b", "c"]
    assert foo["email"] == ["foo@bar.net", "foo@baz.com"]
    assert bar["name"] == "Bar"
    assert bar["affiliation"] == ["Uni C"]
    assert bar["email"] == ["bar@c.edu"]
    assert baz["name"] == "Baz"
    assert baz["affiliation"] == ["Lab E"]
    assert baz["schema:knowsAbout"] is None
    assert baz["email"] is None
    assert data["@type"] == "SoftwareSourceCode"
    assert data["@context"] == ALL_CONTEXTS
    for author in data["author"]:
        assert "name" in author
        assert "email" in author
        if "schema:knowsAbout" not in author:
            author["schema:knowsAbout"] = None
        author["schema:pronouns"] = "they/them"
