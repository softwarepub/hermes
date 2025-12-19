# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen
# SPDX-FileContributor: Michael Fritzsche

from datetime import date
import pytest

from hermes.model.types.ld_list import ld_list
from hermes.model.types.ld_dict import ld_dict


def test_undefined_list():
    with pytest.raises(ValueError):
        ld_list({}, key="foo")
    with pytest.raises(ValueError):
        ld_list([{"@set": [{"@value": "bacon"}]}], key="foo")
    with pytest.raises(ValueError):
        ld_list([{"@value": "bacon"}], key="@type")
    with pytest.raises(ValueError):
        ld_list(["bacon"], key="eggs")
    with pytest.raises(ValueError):
        ld_list([{"@list": ["a", "b"]}])  # no given key


def test_list_basics():
    li_data = [{"@list": [{"@value": "bar"}]}]
    li = ld_list(li_data, key="foo")
    assert li._data is li_data
    assert li.item_list is li_data[0]["@list"]
    li_data = [{"@graph": [{"@value": "bar"}]}]
    li = ld_list(li_data, key="foo")
    assert li._data is li_data
    assert li.item_list is li_data[0]["@graph"]
    li_data = [{"@value": "bar"}]
    li = ld_list(li_data, key="foo")
    assert li._data is li_data
    assert li.item_list is li_data
    assert li.container_type == "@set"


def test_build_in_get():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}], key="name")
    assert li[0] == "foo" and li[-1] == "foobar"
    assert li[:2] == ["foo", "bar"] and li[1:-1] == ["bar"]
    assert li[::2] == ["foo", "foobar"] and li[::-1] == ["foobar", "bar", "foo"]

    li = ld_list([{"@list": [{"@type": "A", "schema:name": "a"}, {"@list": [{"@type": "A", "schema:name": "a"}]}]}],
                 key="schema:person")
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


def test_build_in_set_complex():
    di = ld_dict([{"https://schema.org/name": [{"@list": [{"@value": "c"}]}]}],
                 context=[{"schema": "https://schema.org/"}])
    temp = di["schema:name"]
    di["schema:name"][0] = {"@list": ["a", "b"]}
    assert di["schema:name"][0] == ["a", "b"] and temp._data is di["schema:name"]._data
    li = ld_list([], key="schema:time", context=[{"schema": "https://schema.org/"}])
    date_obj = date(year=2025, month=12, day=31)
    li.append(date_obj)
    assert li.item_list == [{"@value": date_obj.isoformat(), "@type": "https://schema.org/Date"}]
    li[0:1] = ["a", "b", "c"]
    assert li == ["a", "b", "c"]
    li[0:3:2] = [["aa", "bb"]]
    assert li == ["aa", "b", "bb"]


def test_build_in_del():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}],
                 key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    del li[0:3:2]
    assert li == ["bar"]
    del li[0]
    assert li == []
    di = ld_dict([{}], context=[{"schema": "https://schema.org/"}])
    di["schema:name"] = [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]
    li = di["schema:name"]
    del li[0]
    assert len(di["schema:name"]) == 2
    di = ld_dict([{}], context=[{"schema": "https://schema.org/"}])
    di["schema:name"] = [{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}]
    li = di["schema:name"]
    del di["schema:name"][0:3:2]
    assert len(di["schema:name"]) == 1 and len(li) == 1


def test_build_in_len():
    assert len(ld_list([{"@list": []}], key="foo")) == 0
    assert len(ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}], key="foo")) == 3


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
    li.append(ld_list([{"@value": "foo"}], key="https://schema.org/name"))
    assert isinstance(li[0], ld_list) and li[0].container_type == "@list"
    li = ld_list([{"@graph": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append({"schema:name": "foo"})
    assert li[0] == {"https://schema.org/name": "foo"} and len(li) == 1
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
    li = ld_list([], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    assert [] in li
    li.append("foo")
    li.append({"@type": "A", "schema:name": "a"})
    assert "foo" in li and {"@type": "A", "schema:name": "a"} in li
    assert {"@value": "foo"} in li and {"@type": "A", "https://schema.org/name": "a"} in li
    assert ["foo", {"@type": "A", "schema:name": "a"}] in li
    assert [{"@list": ["foo", {"@type": "A", "schema:name": "a"}]}] not in li
    li.append({"@id": "schema:foo", "schema:name": "foo"})
    assert {"@id": "schema:foo"} in li and {"@id": "schema:foo", "schema:name": "foobar"} in li
    assert {"schema:name": "foo"} in li
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append("foo")
    assert "foo" in li


def test_build_in_comparison():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li.append({"@id": "foo", "schema:bar": "foobar"})
    assert [{"@list": [{"@id": "foo", "schema:bar": "barfoo"}]}] == li
    assert [{"@list": [{"@id": "bar", "schema:bar": "foobar"}]}] != li
    assert [{"@set": [{"@id": "foo", "schema:bar": "barfoo"}]}] == li
    assert [{"@graph": [{"@id": "foo", "schema:bar": "barfoo"}]}] == li
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li2 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema2": "https://schema.org/"}])
    assert li == [] and [] == li
    assert li == li2
    li.append("foo")
    li.append({"@type": "A", "schema:name": "a"})
    assert li != li2
    assert ["foo", {"@type": "A", "schema:name": "a"}] == li
    assert ["foo"] != li2
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
    li2 = ld_list([], key="@type", context=[{"schema": "https://schema.org/"}])
    li2.append("schema:name")
    assert li != li2
    li = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li2 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema2": "https://schema.org/"}])
    li.append("foo")
    li2.append("bar")
    assert li != li2
    li[0] = {"@type": "schema:foo", "@value": "bar"}
    assert li != li2
    li[0] = {"@type": "schema:foobar", "@value": "bar"}
    assert li != li2
    li = ld_list([], key="https://schema.org/name", context=[{"schema": "https://schema.org/"}])
    li2 = ld_list([{"@list": []}], key="https://schema.org/name", context=[{"schema2": "https://schema.org/"}])
    li.extend(["foo", "bar"])
    li2.extend(["bar", "foo"])
    assert li == li2
    li.append("bar")
    li2.append("foo")
    assert li != li2


def test_hopcroft_karp():
    ver1 = {0, 1, 2, 3, 4}
    ver2 = {10, 11, 12, 13, 14}
    edges = {0: (10, 11), 1: (10, 14), 2: (12, 13), 3: (10, 14), 4: tuple([11])}
    assert ld_list._hopcroft_karp(ver1, ver2, edges) == 4
    edges[4] = (11, 13)
    assert ld_list._hopcroft_karp(ver1, ver2, edges) == 5
    ver1 = {0, 1, 2, 3, 4}
    ver2 = {(0, 1, 3), (0, 4), (2, ), (2, 4), (1, 3)}
    edges = {
        0: ((0, 1, 3), (0, 4)), 1: ((0, 1, 3), (1, 3)), 2: ((2,), (2, 4)), 3: ((0, 1, 3), (1, 3)), 4: ((0, 4), (2, 4))
    }
    assert ld_list._hopcroft_karp(ver1, ver2, edges) == 5


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
    li.append(ld_dict([{"@type": ["A"], "https://schema.org/name": [{"@value": "a"}]}], parent=li))
    li.append(["a"])
    assert li[1]["@type"].item_list == ["A"]
    assert li.to_python() == ["foo", {"@type": ["A"], "schema:name": ["a"]}, ["a"]]


def test_is_ld_list():
    assert not any(ld_list.is_ld_list(item) for item in [1, "", [], {}, {"@list": []}, [{}], [{"a": "b"}]])
    assert not any(ld_list.is_ld_list(item) for item in [[{"@list": ""}], [{"@list": ["a"]}, {"@list": ["b"]}]])
    assert all(ld_list.is_ld_list([{container_type: []}]) for container_type in ["@list", "@set", "@graph"])


def test_is_container():
    assert not any(ld_list.is_container(item) for item in [1, "", [], {}, {"a": "b"}])
    assert not any(ld_list.is_container(item) for item in [ld_dict([{"a": "b"}]),
                                                           ld_list([{"@list": [{"@value": "a"}]}], key="foo")])
    assert not any(ld_list.is_container({"@list": value}) for value in ["", 1, {}])
    assert all(ld_list.is_container({container_type: []}) for container_type in ["@list", "@graph", "@set"])


def test_from_list():
    with pytest.raises(ValueError):
        ld_list.from_list([], key="@type", container_type="@list")
    with pytest.raises(ValueError):
        ld_list.from_list([], container_type="foo")
    li = ld_list.from_list([], key="schema:foo")
    assert li.item_list == li.context == [] and li.parent is li.index is None and li.key == "schema:foo"
    assert li._data == [] and li.container_type == "@set"
    li = ld_list.from_list([], parent=li, key="schema:name", context=[{"schema": "https://schema.org/"}])
    assert li.item_list == [] and li.parent is None and li.key == "schema:foo"
    assert li.index is None and li.context == []
    li_data = ["a", {"@value": "b"}]
    li = ld_list.from_list(li_data, parent=None, key="https://schema.org/name",
                           context=[{"schema": "https://schema.org/"}])
    assert li.item_list == [{"@value": "a"}, {"@value": "b"}] and li.parent is None
    assert li.key == "https://schema.org/name" and li.index is None
    assert li.context == [{"schema": "https://schema.org/"}]
    assert li.item_list is not li_data  # as li_data is expected to change they should not be the same object


def test_get_item_list_from_container():
    assert ld_list.get_item_list_from_container({"@list": ["a"]}) == ["a"]
    assert ld_list.get_item_list_from_container({"@set": ["a"]}) == ["a"]
    assert ld_list.get_item_list_from_container({"@graph": ["a"]}) == ["a"]
    with pytest.raises(ValueError):
        ld_list.get_item_list_from_container(["a"])
    with pytest.raises(ValueError):
        ld_list.get_item_list_from_container({"@list": [], "@set": []})
    with pytest.raises(ValueError):
        ld_list.get_item_list_from_container({"@list": {}})
    with pytest.raises(ValueError):
        ld_list.get_item_list_from_container({"foo": []})
