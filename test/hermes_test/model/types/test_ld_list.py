# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen
# SPDX-FileContributor: Michael Fritzsche

import pytest

from hermes.model.types.ld_list import ld_list
from hermes.model.types.ld_dict import ld_dict


def test_undefined_list():
    with pytest.raises(ValueError):
        ld_list([{}])
    with pytest.raises(ValueError):
        ld_list([{"spam": [{"@value": "bacon"}]}])
    with pytest.raises(ValueError):
        ld_list([{"@list": [0], "spam": [{"@value": "bacon"}]}])
    with pytest.raises(ValueError):
        ld_list([{"@list": ["a", "b"], "@set": ["foo", "bar"]}])
    with pytest.raises(ValueError):
        ld_list([{"@list": ["a", "b"]}, {"@set": ["foo", "bar"]}])


def test_list_basics():
    li = ld_list([{"@list": [0]}])
    assert li._data == [{"@list": [0]}]
    assert li.item_list == [0]


def test_build_in_get():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}], key="name")
    assert li[0] == "foo" and li[-1] == "foobar"
    assert li[:2] == ["foo", "bar"] and li[1:-1] == ["bar"]
    assert li[::2] == ["foo", "foobar"] and li[::-1] == ["foobar", "bar", "foo"]

    li = ld_list([{"@list": [{"@type": "A", "schema:name": "a"}, {"@list": [{"@type": "A", "schema:name": "a"}]}]}])
    assert isinstance(li[0], ld_dict) and li[0].data_dict == {"@type": "A", "schema:name": "a"} and li[0].index == 0
    assert isinstance(li[1], ld_list) and li[1].item_list == [{"@type": "A", "schema:name": "a"}] and li[1].index == 1
    assert li[1].key == li.key


def test_build_in_set():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}],
                 key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li[0] = "bar"
    li[-1] = "barfoo"
    assert li.item_list[0] == {"@value": "bar"} and li.item_list[-1] == {"@value": "barfoo"}
    li[:2] = ["fo", "ar"]
    assert li.item_list == [{"@value": "fo"}, {"@value": "ar"}, {"@value": "barfoo"}]
    li[1:-1] = ["br"]
    assert li.item_list == [{"@value": "fo"}, {"@value": "br"}, {"@value": "barfoo"}]
    li[::2] = ["oo", "fooba"]
    assert li.item_list == [{"@value": "oo"}, {"@value": "br"}, {"@value": "fooba"}]
    li[::-1] = ["foobar", "bar", "foo"]
    assert li.item_list == [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]
    with pytest.raises(ValueError):
        li[::2] = "foo"
    with pytest.raises(TypeError):
        li[:2] = 1
    li[0] = ld_dict([{"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "a"}]}], parent=li,
                    key=li.key)
    assert isinstance(li[0], ld_dict)
    assert li[0].data_dict == {"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "a"}]}
    li[0] = {"@type": "schema:Thing", "schema:name": "b"}
    assert isinstance(li[0], ld_dict)
    assert li[0].data_dict == {"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "b"}]}
    li[0] = ld_list.from_list([{"@type": "schema:Thing", "schema:name": "a"}], parent=li, key=li.key)
    assert isinstance(li[0], ld_list)
    assert li[0].item_list == [{"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "a"}]}]
    li[0] = {"@set": [{"@type": "schema:Thing", "schema:name": "b"}]}
    assert isinstance(li[0], ld_list)
    assert li[0].item_list == [{"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "b"}]}]
    li[0] = [{"@type": "schema:Thing", "schema:name": "b"}]
    assert isinstance(li[0], ld_list)
    assert li[0].item_list == [{"@type": ["https://schema.org/Thing"], "https://schema.org/name": [{"@value": "b"}]}]


def test_build_in_len():
    assert len(ld_list([{"@list": []}])) == 0
    assert len(ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}])) == 3


def test_build_in_iter():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]},
                             {"@list": [{"@value": "bar"}]}]}], key="https://schema.org/name",
                 context=[{"schema": "https://schema.org/"}])
    li = [val for val in li]
    assert li[0] == "foo"
    assert li[1].data_dict == {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]} and li[1].index == 1
    assert isinstance(li[2], ld_list) and li[2].item_list == [{"@value": "bar"}] and li[2].index == 2
    assert li[2].key == "https://schema.org/name"


def test_append():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append("foo")
    assert li[0] == "foo" and li.item_list[0] == {"@value": "foo"} and len(li) == 1
    li.append("bar")
    assert li[0:2] == ["foo", "bar"] and li.item_list[1] == {"@value": "bar"} and len(li) == 2
    li.append(ld_dict.from_dict({"@type": "A", "schema:name": "a"}, parent=li, key=li.key))
    assert li.item_list[2] == {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]} and len(li) == 3
    li.append({"@type": "A", "schema:name": "a"})
    assert li.item_list[2] == li.item_list[3]
    li.append(ld_list([{"@list": [{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}]}], parent=li,
                      key=li.key))
    li.append([{"@type": "A", "schema:name": "a"}])
    li.append(2 * [{"@type": "A", "schema:name": "a"}])
    assert 2 * li[4].item_list == 2 * li[5].item_list == li[6].item_list


def test_build_in_contains():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append("foo")
    li.append({"@type": "A", "schema:name": "a"})
    assert "foo" in li and {"@type": "A", "schema:name": "a"} in li
    assert {"@value": "foo"} in li and {"@type": "A", "https://schema.org/name": "a"} in li


def test_build_in_comparison():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li2 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema2": "https://schema.org/"}])
    assert li == [] and [] == li
    assert li == li2
    li.append("foo")
    li.append({"@type": "A", "schema:name": "a"})
    assert li != li2 and ["foo", {"@type": "A", "schema:name": "a"}] == li and ["foo"] != li2
    assert ["foo", {"@type": "A", "https://schema.org/name": "a"}] == li
    li2.extend(["foo", {"@type": "A", "schema2:name": "a"}])
    assert li == li2
    li3 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li3.extend([{"@type": "A", "schema:name": "a"}, "foo"])
    assert li != li3
    assert not li == 3
    assert li != 3
    li = ld_list([{"@list": []}], key="https://schema.org/Person", context=[{"schema": "https://schema.org/"}])
    li.append({"@id": "foo"})
    assert li == [{"@id": "foo"}] and li == [{"@id": "foo", "schema:name": "bar"}] and li == {"@list": [{"@id": "foo"}]}
    li2 = ld_list([{"@list": []}], key="@type", context=[{"schema": "https://schema.org/"}])
    li2.append("schema:name")
    assert li != li2
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li2 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema2": "https://schema.org/"}])
    li.append("foo")
    li2.append("bar")
    assert li != li2
    li[0] = {"@type": "foo", "@value": "bar"}
    assert li != li2
    li[0] = {"@type": "foobar", "@value": "bar"}
    assert li != li2


def test_extend():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.extend([])
    assert len(li) == 0
    li.extend(["foo"])
    assert li[0] == "foo" and li.item_list[0] == {"@value": "foo"} and len(li) == 1
    li.extend(["bar"])
    assert li[0:2] == ["foo", "bar"] and li.item_list[1] == {"@value": "bar"} and len(li) == 2
    li.extend([ld_dict([{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}])])
    assert li[-1].data_dict == {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]} and len(li) == 3

    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.extend(["foo", "bar", ld_dict([{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}])])
    assert li[0:2] == ["foo", "bar"] and li.item_list[0:2] == [{"@value": "foo"}, {"@value": "bar"}]
    assert li[-1].data_dict == {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]} and len(li) == 3

    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append("foo")
    li.extend(["bar", ld_dict([{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}])])
    assert li[0:2] == ["foo", "bar"] and li.item_list[0:2] == [{"@value": "foo"}, {"@value": "bar"}]
    assert li[-1].data_dict == {"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]} and len(li) == 3


def test_to_python():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append("foo")
    li.append(ld_dict([{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}]))
    li.append(["a"])
    assert li[1]["@type"].item_list == ["A"]
    assert li.to_python() == ["foo", {"@type": ["A"], "schema:name": ["a"]}, ["a"]]


def test_is_ld_list():
    assert not any(ld_list.is_ld_list(item) for item in [1, "", [], {}, {"@list": []}, [{}], [{"a": "b"}]])
    assert not any(ld_list.is_ld_list(item) for item in [[{"@list": ""}], [{"@list": ["a"]}, {"@list": ["b"]}]])
    assert all(ld_list.is_ld_list([{container_type: []}]) for container_type in ["@list", "@set", "@graph"])


def test_is_container():
    assert not any(ld_list.is_container(item) for item in [1, "", [], {}, {"a": "b"}])
    assert not any(ld_list.is_container(item) for item in [ld_dict([{"a": "b"}]), ld_list([{"@list": ["a"]}])])
    assert not any(ld_list.is_container({"@list": value}) for value in ["", 1, {}])
    assert all(ld_list.is_container({container_type: []}) for container_type in ["@list", "@graph", "@set"])


def test_from_list():
    li = ld_list.from_list([])
    assert li.item_list == li.context == [] and li.parent is li.key is li.index is None
    assert li._data == [{"@list": []}]
    li = ld_list.from_list([], parent=li, key="schema:name", context=[{"schema": "https://schema.org/"}])
    assert li.item_list == [] and li.parent is not None and li.key == "schema:name"
    assert li.index is None and li.context == [{"schema": "https://schema.org/"}]
    li = ld_list.from_list(["a", {"@value": "b"}], parent=None, key="https://schema.org/name",
                           context=[{"schema": "https://schema.org/"}])
    assert li.item_list == [{"@value": "a"}, {"@value": "b"}] and li.parent is None
    assert li.key == "https://schema.org/name" and li.index is None
    assert li.context == [{"schema": "https://schema.org/"}]


def test_get_item_list_from_container():
    assert ld_list.get_item_list_from_container({"@list": ["a"]}) == ["a"]
    assert ld_list.get_item_list_from_container({"@set": ["a"]}) == ["a"]
    assert ld_list.get_item_list_from_container({"@graph": ["a"]}) == ["a"]
    with pytest.raises(ValueError):
        ld_list.get_item_list_from_container(["a"])
