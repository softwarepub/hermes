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
        ld_list([{"@list": ["a", "b"], "@set": ["foo", "bar"]}])
    with pytest.raises(ValueError):
        ld_list([{"@list": ["a", "b"]}, {"@set": ["foo", "bar"]}])


def test_list_basics():
    li = ld_list([{"@list": [0], "spam": [{"@value": "bacon"}]}])
    assert li._data == [{"@list": [0], "spam": [{"@value": "bacon"}]}]
    assert li.container == '@list'
    assert li.item_list == [0]


def test_build_in_get():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}])
    assert li[0] == "foo" and li[-1] == "foobar"
    assert li[:2] == ["foo", "bar"] and li[1:-1] == ["bar"]
    assert li[::2] == ["foo", "foobar"] and li[::-1] == ["foobar", "bar", "foo"]

    li = ld_list([{"@list": [{"@type": "A", "schema:name": "a"}]}])
    assert isinstance(li[0], ld_dict) and li[0].data_dict == {"@type": "A", "schema:name": "a"} and li[0].index == 0


def test_build_in_set():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}],
                 key="https://schema.org/name", context={"schema": "https://schema.org/"})
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


def test_build_in_len():
    assert len(ld_list([{"@list": []}])) == 0
    assert len(ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}])) == 3


def test_build_in_iter():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@type": "A", "schema:name": "a"}]}],
                 key="https://schema.org/name", context={"schema": "https://schema.org/"})
    li = [val for val in li]
    assert li[0] == "foo" and li[1].data_dict == {"@type": "A", "schema:name": "a"} and li[1].index == 1


def test_append():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context={"schema": "https://schema.org/"})
    li.append("foo")
    assert li[0] == "foo" and li.item_list[0] == {"@value": "foo"} and len(li) == 1
    li.append("bar")
    assert li[0:2] == ["foo", "bar"] and li.item_list[1] == {"@value": "bar"} and len(li) == 2
    li.append(ld_dict([{"@type": "A", "schema:name": "a"}]))
    assert li[-1].data_dict == {"@type": "A", "schema:name": "a"} and len(li) == 3


def test_extend():
    li = ld_list([{"@list": []}], key="https://schema.org/name", context={"schema": "https://schema.org/"})
    li.extend([])
    assert len(li) == 0
    li.extend(["foo"])
    assert li[0] == "foo" and li.item_list[0] == {"@value": "foo"} and len(li) == 1
    li.extend(["bar"])
    assert li[0:2] == ["foo", "bar"] and li.item_list[1] == {"@value": "bar"} and len(li) == 2
    li.extend([ld_dict([{"@type": "A", "schema:name": "a"}])])
    assert li[-1].data_dict == {"@type": "A", "schema:name": "a"} and len(li) == 3

    li = ld_list([{"@list": []}], key="https://schema.org/name", context={"schema": "https://schema.org/"})
    li.extend(["foo", "bar", ld_dict([{"@type": "A", "schema:name": "a"}])])
    assert li[0:2] == ["foo", "bar"] and li.item_list[0:2] == [{"@value": "foo"}, {"@value": "bar"}]
    assert li[-1].data_dict == {"@type": "A", "schema:name": "a"} and len(li) == 3

    li = ld_list([{"@list": []}], key="https://schema.org/name", context={"schema": "https://schema.org/"})
    li.append("foo")
    li.extend(["bar", ld_dict([{"@type": "A", "schema:name": "a"}])])
    assert li[0:2] == ["foo", "bar"] and li.item_list[0:2] == [{"@value": "foo"}, {"@value": "bar"}]
    assert li[-1].data_dict == {"@type": "A", "schema:name": "a"} and len(li) == 3


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
    assert li.container == "@list" and li.item_list == li.context == [] and li.parent is li.key is li.index is None
    li = ld_list.from_list([], parent=li, key="schema:name", context={"schema": "https://schema.org/"},
                           container="@set")
    assert li.container == "@set" and li.item_list == [] and li.parent is not None and li.key == "schema:name"
    assert li.index is None and li.context == {"schema": "https://schema.org/"}
    li = ld_list.from_list(["a", {"@value": "b"}], parent=None, key="https://schema.org/name",
                           context={"schema": "https://schema.org/"}, container="@graph")
    assert li.container == "@graph" and li.item_list == [{"@value": "a"}, {"@value": "b"}] and li.parent is None
    assert li.key == "https://schema.org/name" and li.index is None and li.context == {"schema": "https://schema.org/"}
