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
    assert metadata["funding"][0] == "foo"


def test_init_nested_object():
    my_software = {
        "schema:softwareName": "MySoftware",
        "foo:egg": "spam",
        "foo:ham": "eggs",
        "maintainer": {"name": "Some Name", "email": "maintainer@example.com"},
        "author": [{"name": "Foo"}, {"name": "Bar"}],
    }
    data = SoftwareMetadata(my_software, extra_vocabs={"foo": "https://foo.bar"})
    assert data["schema:softwareName"][0] == "MySoftware"
    assert data["maintainer"][0]["name"][0] == "Some Name"
    for author in data["author"]:
        for name in author["name"]:
            assert name in ["Foo", "Bar"]


def test_append():
    data = SoftwareMetadata()
    data["foo"].append("a")
    assert type(data["foo"]) is ld_list and data["foo"][0] == "a" and data["foo"].item_list == [{"@value": "a"}]
    data["foo"].append("b")
    assert type(data["foo"]) is ld_list and data["foo"].item_list == [{"@value": "a"}, {"@value": "b"}]
    data["foo"].append("c")
    assert data["foo"].item_list == [{"@value": "a"}, {"@value": "b"}, {"@value": "c"}]
    data = SoftwareMetadata()
    data["foo"].append({"schema:name": "foo"})
    assert type(data["foo"]) is ld_list and type(data["foo"][0]) is ld_dict
    assert data["foo"][0].data_dict == {"http://schema.org/name": [{"@value": "foo"}]}
    data["foo"].append({"schema:name": "foo"})
    assert type(data["foo"]) is ld_list and data["foo"].item_list == 2*[{"http://schema.org/name": [{"@value": "foo"}]}]
    data["foo"].append({"schema:name": "foo"})
    assert data["foo"].item_list == 3 * [{"http://schema.org/name": [{"@value": "foo"}]}]


def test_iterative_assignment():
    # This tests iterative assignments/traversals to edit/appending values
    data = SoftwareMetadata(extra_vocabs={"foo": "https://foo.bar"})
    data["author"] = {"name": "Foo"}
    # Look, a squirrel!
    authors = data["author"]
    assert isinstance(authors, ld_list)
    author1 = authors[0]
    author1["email"] = "author@example.com"
    authors[0] = author1
    authors.append({"name": "Bar", "email": "author2@example.com"})
    assert len(authors) == 2


def test_usage():
    data = SoftwareMetadata()
    data["author"] = {"name": "Foo"}
    data["author"].append({"name": "Bar"})
    data["author"][0]["email"] = "foo@bar.net"
    data["author"][0]["email"].append("foo@baz.com")
    assert len(data["author"]) == 2
    assert len(data["author"][0]["email"]) == 2
    assert len(data["author"][1]["email"]) == 0
    harvest = {
        "authors": [
            {"name": "Foo", "affiliation": ["Uni A", "Lab B"], "kw": ["a", "b", "c"]},
            {"name": "Bar", "affiliation": ["Uni C"], "email": "bar@c.edu"},
            {"name": "Baz", "affiliation": ["Lab E"]},
        ]
    }
    for author in harvest["authors"]:
        for exist_author in data["author"]:
            if author["name"] == exist_author["name"][0]:
                exist_author["affiliation"] = author["affiliation"]
                if "email" in author:
                    exist_author["email"].append(author["email"])
                if "kw" in author:
                    exist_author["schema:knowsAbout"].extend(author["kw"])
                break
        else:
            data["author"].append(author)
    assert len(data["author"]) == 3
    foo, bar, baz = data["author"]
    assert foo["name"][0] == "Foo"
    assert foo["affiliation"].to_python() == ["Uni A", "Lab B"]
    assert foo["schema:knowsAbout"].to_python() == ["a", "b", "c"]
    assert foo["email"].to_python() == ["foo@bar.net", "foo@baz.com"]
    assert bar["name"][0] == "Bar"
    assert bar["affiliation"].to_python() == ["Uni C"]
    assert bar["email"].to_python() == ["bar@c.edu"]
    assert baz["name"][0] == "Baz"
    assert baz["affiliation"].to_python() == ["Lab E"]
    assert len(baz["schema:knowsAbout"]) == 0
    assert len(baz["email"]) == 0
    for author in data["author"]:
        assert "name" in author
        assert "email" in author
        if "schema:knowsAbout" not in author:
            # FIXME: None has to be discussed
            author["schema:knowsAbout"] = None
        author["schema:pronouns"] = "they/them"
