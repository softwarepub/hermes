# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
# SPDX-FileContributor: Michael Fritzsche <michael.fritzsche@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from hermes.model.types.ld_dict import ld_dict
from hermes.model.types.ld_list import ld_list


def test_dict_basics():
    di = ld_dict([{"foo": "bar", "foobar": "barfoo"}])
    assert di.data_dict == {"foo": "bar", "foobar": "barfoo"}
    assert di.context == []
    assert di.parent is None and di.key is None and di.index is None


def test_malformed_input():
    with pytest.raises(ValueError):
        ld_dict([])

    with pytest.raises(ValueError):
        ld_dict([{"foo": "bar"}, {"bar": "foo"}])


def test_build_in_get():
    di = ld_dict([{"http://schema.org/name": [{"@value": "Manu Sporny"}],
                   "http://schema.org/homepage": [{"@id": "http://manu.sporny.org/"}],
                   "http://schema.org/foo": [{"http://schema.org/foobar": [{"@value": "bar"}],
                                              "http://schema.org/barfoo": [{"@value": "foo"}]}]}],
                 context=[{"schema": "http://schema.org/"}])
    assert isinstance(di["schema:name"], ld_list) and di["schema:name"].item_list == [{"@value": "Manu Sporny"}]
    assert isinstance(di["schema:homepage"], ld_list)
    assert di["schema:homepage"].item_list == [{"@id": "http://manu.sporny.org/"}]
    assert isinstance(di["http://schema.org/foo"], ld_list) and isinstance(di["http://schema.org/foo"][0], ld_dict)
    assert di["http://schema.org/foo"][0].data_dict == {"http://schema.org/foobar": [{"@value": "bar"}],
                                                        "http://schema.org/barfoo": [{"@value": "foo"}]}
    assert isinstance(di["bar"], ld_list) and len(di["bar"]) == 0

    di = ld_dict([{"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}]}],
                 context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    assert di["xmlns:name"].item_list == [{"@value": "Manu Sporny"}]


def test_build_in_set():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di["http://xmlns.com/foaf/0.1/name"] = "Manu Sporny"
    assert di.data_dict == {"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}]}

    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di["xmlns:name"] = "Manu Sporny"
    di["xmlns:homepage"] = {"@id": "http://manu.sporny.org/"}
    assert di.data_dict == {"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}],
                            "http://xmlns.com/foaf/0.1/homepage": [{"@id": "http://manu.sporny.org/"}]}

    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di["xmlns:name"] = ["Manu Sporny", "foo"]
    assert di.data_dict == {"http://xmlns.com/foaf/0.1/name": [{"@list": [{"@value": "Manu Sporny"},
                                                                          {"@value": "foo"}]}]}

    di = ld_dict([{}], context={"schema": "https://schema.org/"})
    di["@type"] = "schema:Thing"
    di["schema:result"] = {"@type": "schema:Action", "schema:name": "Test"}
    assert di.data_dict == {
        "@type": ["https://schema.org/Thing"],
        "https://schema.org/result": [{
            "@type": ["https://schema.org/Action"],
            "https://schema.org/name": [{"@value": "Test"}]
        }]
    }

    di = ld_dict([{}], context={"schema": "https://schema.org/"})
    di["@type"] = "schema:Thing"
    di["schema:result"] = {"@type": "schema:Action", "schema:error": {"@type": "schema:Thing", "schema:name": "foo"}}
    assert di.data_dict == {
        "@type": ["https://schema.org/Thing"],
        "https://schema.org/result": [{
            "@type": ["https://schema.org/Action"],
            "https://schema.org/error": [{
                "@type": ["https://schema.org/Thing"],
                "https://schema.org/name": [{"@value": "foo"}]
            }]
        }]
    }

    di = ld_dict([{}], context={"schema": "https://schema.org/"})
    di["@type"] = "schema:Thing"
    di["schema:result"] = {"@type": "schema:Action", "schema:error": {"@type": "schema:Thing", "schema:name": ["foo",
                                                                                                               "bar"]}}
    assert di.data_dict == {
        "@type": ["https://schema.org/Thing"],
        "https://schema.org/result": [{
            "@type": ["https://schema.org/Action"],
            "https://schema.org/error": [{
                "@type": ["https://schema.org/Thing"],
                "https://schema.org/name": [{"@value": "foo"}, {"@value": "bar"}]
            }]
        }]
    }
    assert isinstance(di["schema:result"][0]["schema:error"][0]["schema:name"], ld_list)


def test_build_in_delete():
    di = ld_dict([{"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}],
                   "http://xmlns.com/foaf/0.1/homepage": [{"@id": "http://manu.sporny.org/"}]}],
                 context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    del di["http://xmlns.com/foaf/0.1/name"]
    del di["xmlns:homepage"]
    assert di.data_dict == {}


def test_build_in_contains():
    di = ld_dict([{"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}],
                   "http://xmlns.com/foaf/0.1/homepage": [{"@id": "http://manu.sporny.org/"}]}],
                 context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    assert "http://xmlns.com/foaf/0.1/name" in di and "xmlns:homepage" in di
    assert "xmlns:foo" not in di and "homepage" not in di and "foo" not in di


def test_get():
    di = ld_dict([{"https://schema.org/name": [{"@value": "Manu Sporny"}]}], context={"schema": "https://schema.org/"})
    assert di.get("https://schema.org/name").item_list == [{"@value": "Manu Sporny"}]
    assert di.get("schema:name").item_list == [{"@value": "Manu Sporny"}]
    assert di.get("bar", None) is None
    assert isinstance(di["bar"], ld_list) and len(di["bar"]) == 0


def test_update():
    di = ld_dict([{"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}],
                   "http://xmlns.com/foaf/0.1/homepage": [{"@id": "http://manu.sporny.org/"}]}],
                 context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di.update({})
    assert di.data_dict == {"http://xmlns.com/foaf/0.1/name": [{"@value": "Manu Sporny"}],
                            "http://xmlns.com/foaf/0.1/homepage": [{"@id": "http://manu.sporny.org/"}]}

    di.update({"http://xmlns.com/foaf/0.1/name": "foo", "xmlns:homepage": {"@id": "bar"},
               "xmlns:foo": {"xmlns:foobar": "bar", "http://xmlns.com/foaf/0.1/barfoo": {"@id": "foo"}}})
    assert di.data_dict == {"http://xmlns.com/foaf/0.1/name": [{"@value": "foo"}],
                            "http://xmlns.com/foaf/0.1/homepage": [{"@id": "bar"}],
                            "http://xmlns.com/foaf/0.1/foo": [{"http://xmlns.com/foaf/0.1/foobar": [{"@value": "bar"}],
                                                               "http://xmlns.com/foaf/0.1/barfoo": [{"@id": "foo"}]}]}
    with pytest.raises(AttributeError):
        di.update(["", ""])


def test_keys():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di.update({"http://xmlns.com/foaf/0.1/name": "Manu Sporny", "xmlns:homepage": {"@id": "http://manu.sporny.org/"}})
    assert {*di.keys()} == {"http://xmlns.com/foaf/0.1/name", "http://xmlns.com/foaf/0.1/homepage"}


def test_compact_keys():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di.update({"http://xmlns.com/foaf/0.1/name": "Manu Sporny", "xmlns:homepage": {"@id": "http://manu.sporny.org/"}})
    assert {*di.compact_keys()} == {"xmlns:name", "xmlns:homepage"}

    di = ld_dict([{}], context={"homepage": "http://xmlns.com/foaf/0.1/homepage"})
    di.update({"http://xmlns.com/foaf/0.1/name": "Manu Sporny",
               "http://xmlns.com/foaf/0.1/homepage": {"@id": "http://manu.sporny.org/"}})
    assert {*di.compact_keys()} == {"http://xmlns.com/foaf/0.1/name", "homepage"}

    di = ld_dict([{}], context={"xmls": "http://xmlns.com/foaf/0.1/", "homepage": "http://xmlns.com/foaf/0.1/homepage"})
    di.update({"http://xmlns.com/foaf/0.1/name": "Manu Sporny",
               "http://xmlns.com/foaf/0.1/homepage": {"@id": "http://manu.sporny.org/"}})
    assert {*di.compact_keys()} == {"xmls:name", "homepage"}


def test_items():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    inner_di = ld_dict([{}], parent=di)
    inner_di.update({"xmlns:foobar": "bar", "http://xmlns.com/foaf/0.1/barfoo": {"@id": "foo"}})
    di.update({"http://xmlns.com/foaf/0.1/name": "foo", "xmlns:homepage": {"@id": "bar"}, "xmlns:foo": inner_di})
    items = [*di.items()]
    assert (items[0][0], items[1][0]) == ("http://xmlns.com/foaf/0.1/name", "http://xmlns.com/foaf/0.1/homepage")
    assert (items[0][1].item_list, items[1][1].item_list) == ([{"@value": "foo"}], [{"@id": "bar"}])
    assert items[2][0] == "http://xmlns.com/foaf/0.1/foo" and isinstance(items[2][1], ld_list)
    assert items[2][1][0].data_dict == {"http://xmlns.com/foaf/0.1/foobar": [{"@value": "bar"}],
                                        "http://xmlns.com/foaf/0.1/barfoo": [{"@id": "foo"}]}


def test_ref():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    di.update({"@id": "http://xmlns.com/foaf/0.1/homepage", "xmlns:name": "homepage"})
    assert di.ref == {"@id": "http://xmlns.com/foaf/0.1/homepage"}

    di = ld_dict([{"http://xmlns.com/foaf/0.1/name": "foo"}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    with pytest.raises(KeyError):
        di.ref


def test_to_python():
    di = ld_dict([{}], context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    inner_di = ld_dict([{}], parent=di)
    inner_di.update({"xmlns:foobar": "bar", "http://xmlns.com/foaf/0.1/barfoo": {"@id": "foo"}})
    di.update({"http://xmlns.com/foaf/0.1/name": "foo", "xmlns:homepage": {"@id": "bar"}, "xmlns:foo": inner_di})
    assert di.to_python() == {"xmlns:name": ["foo"], "xmlns:homepage": ["bar"],
                              "xmlns:foo": [{"xmlns:foobar": ["bar"], "xmlns:barfoo": ["foo"]}]}


def test_from_dict():
    di = ld_dict.from_dict({"@type": "xmlns:hompage", "@id": "foo"})
    assert di.data_dict == {"@type": ["xmlns:hompage"], "@id": "foo"}
    assert di.active_ctx == {"mappings": {}} and di.context == di.full_context == []
    assert di.index is di.key is di.parent is None

    di = ld_dict.from_dict({"http://xmlns.com/foaf/0.1/name": [{"@value": "foo"}],
                            "http://xmlns.com/foaf/0.1/foo": [{"http://xmlns.com/foaf/0.1/barfoo": [{"@id": "foo"}],
                                                               "http://xmlns.com/foaf/0.1/fooba": [{"@value": "ba"}]}]})
    assert di.active_ctx == {"mappings": {}} and di.context == di.full_context == []
    assert di.index is di.key is di.parent is None

    di = ld_dict.from_dict({"@type": "xmlns:hompage", "@id": "foo"}, ld_type="xmlns:webpage")
    assert di.data_dict == {"@type": ["xmlns:webpage", "xmlns:hompage"], "@id": "foo"}
    assert di.active_ctx == {"mappings": {}} and di.context == di.full_context == []
    assert di.index is di.key is di.parent is None

    di = ld_dict.from_dict({"@context": {"schema": "https://schema.org/"}, "@type": "schema:Thing", "@id": "foo"})
    assert di.data_dict == {"@type": ["https://schema.org/Thing"], "@id": "foo"}
    assert di.context == di.full_context == {"schema": "https://schema.org/"}
    assert di.index is di.key is di.parent is None

    outer_di = di
    di = ld_dict.from_dict({"@context": {"schema": "https://schema.org/"}, "@type": "schema:Action",
                            "schema:name": "foo"},
                           parent=outer_di, key="schema:result")
    assert di.data_dict == {"@type": ["https://schema.org/Action"], "https://schema.org/name": [{"@value": "foo"}]}
    assert di.full_context == 2 * [{"schema": "https://schema.org/"}]
    assert di.context == {"schema": "https://schema.org/"} and di.key == "schema:result" and di.index is None

    outer_di = di
    di = ld_dict.from_dict({"@context": {"schema": "https://schema.org/"}, "@type": "schema:Thing",
                            "schema:name": "foo"},
                           parent=outer_di, key="schema:error")
    assert di.data_dict == {"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "foo"}]}
    assert di.full_context == 3 * [{"schema": "https://schema.org/"}]
    assert di.context == {"schema": "https://schema.org/"} and di.key == "schema:error" and di.index is None

    di = ld_dict.from_dict({"@type": "schema:Thing", "schema:name": "foo"}, parent=outer_di, key="schema:error")
    assert di.data_dict == {"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "foo"}]}
    assert di.full_context == 2 * [{"schema": "https://schema.org/"}]
    assert di.context == [] and di.key == "schema:error" and di.index is None

    di = ld_dict.from_dict({"@context": {"schema": "https://schema.org/"}, "@type": "schema:Thing", "xmlns:name": "fo"},
                           context={"xmlns": "http://xmlns.com/foaf/0.1/"})
    assert di["http://xmlns.com/foaf/0.1/name"] == di["xmlns:name"] == "fo"
    assert di.context == {"schema": "https://schema.org/", "xmlns": "http://xmlns.com/foaf/0.1/"}


def test_is_ld_dict():
    assert not any(ld_dict.is_ld_dict(item) for item in [{}, {"foo": "bar"}, {"@id": "foo"}])
    assert not any(ld_dict.is_ld_dict(item) for item in [[{"@id": "foo"}], [{"@set": "foo"}], [{}, {}], [], [""]])
    assert all(ld_dict.is_ld_dict([item]) for item in [{"@id": "foo", "foobar": "bar"}, {"foo": "bar"}])


def test_is_json_dict():
    assert not any(ld_dict.is_json_dict(item) for item in [1, "", [], {""}, ld_dict([{}])])
    assert not any(ld_dict.is_json_dict({key: [], "foo": "bar"}) for key in ["@set", "@graph", "@list", "@value"])
    assert not ld_dict.is_json_dict({"@id": "foo"})
    assert ld_dict.is_json_dict({"@id": "foo", "foobar": "bar"})
    assert ld_dict.is_json_dict({"foo": "bar"})
