# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

import pytest
import tomlkit

from hermes.commands.harvest.toml import TomlHarvestPlugin


@pytest.mark.parametrize("in_data, out_data", [
    ({"givenName": "Tom"}, {"givenName": "Tom"}), ({"a": "b"}, {}),
    ({"givenName": "Tom","a": "b"}, {"givenName": "Tom"}), ({}, {})
])
def test_remove_forbidden_keys(in_data, out_data):
    assert TomlHarvestPlugin.remove_forbidden_keys(in_data) == out_data

@pytest.mark.parametrize("in_data, out_data", [
    ({"givenName": "Tom"}, {"givenName": "Tom"}), ({"a": "b"}, {}),
    ({"givenName": "Tom","a": "b"}, {"givenName": "Tom"}), ({}, {}),
    ([{"givenName": "Tom"}], [{"givenName": "Tom"}]),
    ([{"givenName": "Tom"}, {"a": "b"}], [{"givenName": "Tom"}]),
    ([{}, {"givenName": "Tom"}, {"a": "b"}], [{"givenName": "Tom"}]),
    ([{}], []), ([{"b":"c"}], []), ([], [])
])
def test_handle_person(in_data, out_data):
    assert TomlHarvestPlugin.handle_person_in_unknown_format(in_data) == out_data

@pytest.mark.parametrize("in_data", [
    (15), ([{}, (15)]), (None)
])
def test_handle_person_with_error(in_data):
    with pytest.raises(ValueError):
        TomlHarvestPlugin.handle_person_in_unknown_format(in_data)

@pytest.fixture(scope="session")
def toml_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "test.toml"
    return fn

@pytest.mark.parametrize("in_data, out_data", [
    ({}, {}), ({"project": {"name":"a"}}, {"name": "a"}),
    ({"tool": {"poetry": {"name":"a"}}}, {"name": "a"}),
    ({"project":{"name":"a"}, "a":{"b":"c"}}, {"name":"a"}),
    ({"project":{"name":"a", "requires-python":">3.7"}}, {"name":"a", "runtimePlatform":"Python >3.7"}),
    ({"project":{"authors":{"givenName":"a"}}}, {"author":{"givenName":"a", "@type":"Person"}}),
    ({"project":{"authors":[{"givenName":"a"}, {"givenName":"a"}]}}, {"author":[{"givenName":"a", "@type":"Person"}, {"givenName":"a", "@type":"Person"}]}),
    ({"project":{"authors":{"givenName":"a", "a":"b"}}}, {"author":{"givenName":"a", "@type":"Person"}}),
    ({"project":{"authors":{"a":"b"}}}, {}),
    ({"project":{"authors":[{"a":"a"}, {"givenName":"a"}]}}, {"author":{"givenName":"a", "@type":"Person"}}),
    ({"project":{"authors":[{"a":"b"}]}}, {}),
    ({"project":{"authors":["abc def<abc.def@dlr.com>"]}}, {"author":{"name":"abc def", "email": "abc.def@dlr.com", "@type": "Person"}}),
    ({"project":{"authors":"abc def<abc.def@dlr.com>"}}, {"author":{"name":"abc def", "email": "abc.def@dlr.com", "@type": "Person"}})
])
def test_read_from_toml(in_data, out_data, toml_file):
    with open(toml_file, "w", encoding="utf8") as fp:
        tomlkit.dump(in_data, fp)
    assert TomlHarvestPlugin.read_from_toml(str(toml_file)) == out_data

@pytest.mark.parametrize("in_data", [
    ({"project": {"authors":1}}), ({"tool": {"poetry": {"authors":1}}}),
    ({"project": {"authors":[1]}}), ({"tool": {"poetry": {"authors":[1]}}}),
    ({"project": {"name":"a"}, "tool": {"poetry": {"name":"a"}}}),
    ({"project": {"authors":["as<as>as"]}}),
    ({"project": {"authors":"as<as>as"}})
])
def test_read_from_toml_with_error(in_data, toml_file):
    toml.dump(in_data, open(toml_file, "w", encoding="utf8"))
    with pytest.raises(ValueError):
        TomlHarvestPlugin.read_from_toml(str(toml_file))
