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
        ld_list([{"spam": [{"@value": "bacon"}]}])
    with pytest.raises(ValueError):
        ld_list([{"@list": ["a", "b"], "@set": ["foo", "bar"]}])


@pytest.mark.dev
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

    li = ld_list([{"@list": [ld_dict([{"@type": "A", "schema:name": "a"}])]}])
    assert isinstance(li[0], ld_dict) and li[0].data_dict == {"@type": "A", "schema:name": "a"} and li[0].index == 0


def test_build_in_set():
    li = ld_list([{"@list": [{"@value": "foo"}, {"@value": "bar"}, {"@value": "foobar"}]}], key="https://schema.org/name", context={"schema": "https://schema.org/"})
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
