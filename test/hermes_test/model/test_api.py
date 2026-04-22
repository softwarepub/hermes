# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche
# SPDX-FileContributor: Stephan Druskat

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
    assert data["schema:softwareName"] == ["MySoftware"]
    assert len(data["maintainer"]) == 1 and data["maintainer"][0]["name"] == ["Some Name"]
    for author in data["author"]:
        for name in author["name"]:
            assert name in ["Foo", "Bar"]


def test_append():
    data = SoftwareMetadata()
    data.emplace("schema:name")
    data["schema:name"].append("a")
    assert type(data["schema:name"]) is ld_list
    assert data["schema:name"][0] == "a" and data["schema:name"] == ["a"]
    data["schema:name"].append("b")
    assert type(data["schema:name"]) is ld_list and data["schema:name"] == ["a", "b"]
    data.emplace("schema:name")
    data["schema:name"].append("c")
    assert data["schema:name"] == ["a", "b", "c"]

    data = SoftwareMetadata()
    data.setdefault("schema:Person", []).append({"schema:name": "foo"})
    assert type(data["schema:Person"]) is ld_list and type(data["schema:Person"][0]) is ld_dict
    assert data["schema:Person"][0] == {"http://schema.org/name": ["foo"]}
    data["schema:Person"].append({"schema:name": "foo"})
    assert type(data["schema:Person"]) is ld_list
    assert data["schema:Person"] == 2 * [{"http://schema.org/name": ["foo"]}]
    data["schema:Person"].append({"schema:name": "foo"})
    assert data["schema:Person"] == 3 * [{"http://schema.org/name": ["foo"]}]


def test_iterative_assignment():
    # This tests iterative assignments/traversals to edit/appending values
    data = SoftwareMetadata(extra_vocabs={"foo": "https://foo.bar"})
    data["author"] = {"name": "Foo"}
    # Look, a squirrel!
    authors = data["author"]
    assert isinstance(authors, ld_list)
    author1 = authors[0]
    author1["email"] = "author@example.com"
    authors.append({"name": "Bar", "email": "author2@example.com"})
    assert len(authors) == 2
    del authors[0]
    assert len(authors) == 1


def test_usage():
    data = SoftwareMetadata()
    data["author"] = {"name": "Foo"}
    data["author"].append({"name": "Bar"})
    data["author"][0]["email"] = "foo@bar.net"
    data["author"][0]["email"].append("foo@baz.com")
    assert len(data["author"]) == 2
    assert len(data["author"][0]["email"]) == 2
    assert len(data["author"][1].get("email", [])) == 0
    harvest = {
        "authors": [
            {"name": "Foo", "affiliation": ["Uni A", "Lab B"], "kw": ["a", "b", "c"]},
            {"name": "Bar", "affiliation": ["Uni C"], "email": "bar@c.edu", "kw": "egg"},
            {"name": "Baz", "affiliation": ["Lab E"]},
        ]
    }
    for author in harvest["authors"]:
        for exist_author in data.get("author", []):
            if author["name"] in exist_author.get("name", []):
                exist_author["affiliation"] = author["affiliation"]
                if "email" in author:
                    exist_author.emplace("email")
                    exist_author["email"].append(author["email"])
                if "kw" in author:
                    exist_author.emplace("schema:knowsAbout")
                    exist_author["schema:knowsAbout"].extend(author["kw"])
                break
        else:
            data.setdefault("author", []).append(author)
    assert len(data.get("author", [])) == 3
    foo, bar, baz = data["author"]
    assert foo["name"][0] == "Foo"
    assert foo["affiliation"] == ["Uni A", "Lab B"]
    assert foo["schema:knowsAbout"] == ["a", "b", "c"]
    assert foo["email"] == ["foo@bar.net", "foo@baz.com"]
    assert bar["name"][0] == "Bar"
    assert bar["affiliation"] == ["Uni C"]
    assert bar["email"] == ["bar@c.edu"]
    assert baz["name"][0] == "Baz"
    assert baz["affiliation"] == ["Lab E"]
    assert len(baz.get("schema:knowsAbout", [])) == 0
    assert len(baz.get("email", [])) == 0
    for author in data["author"]:
        assert "name" in author
        if "Baz" not in author["name"]:
            assert "email" in author
        if "schema:knowsAbout" not in author:
            # FIXME: None has to be discussed
            author["schema:knowsAbout"] = None
        author["schema:pronouns"] = "they/them"
