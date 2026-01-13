# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Sophie Kernchen
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from datetime import datetime, time

import pytest

from hermes.model.types.ld_container import ld_container
from hermes.model.types.ld_dict import ld_dict

'''we expect user of this class to give the right input data types

example extended json ld:
        [{
      "http://schema.org/name": [{"@value": "bacon"}],
      "eggs": [{"@id": "spam"}],
      "green": [{"@id": "png"}]
        }]
'''


class TestLdContainer:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, httpserver, mock_document):
        cls.url = httpserver.url_for("/")
        httpserver.expect_request("/").respond_with_json({"@context": mock_document.vocabulary(cls.url)})

    def test_container_basic(self):
        cont = ld_container([{"spam": [{"@value": "bacon"}]}])

        assert cont.key is None
        assert cont.context == []
        assert cont._data == [{"spam": [{"@value": "bacon"}]}]
        assert cont.path == ["$"]

    def test_container_ld_value(self):
        cont = ld_container([{"spam": [{"@value": "bacon"}]}])

        assert cont.ld_value == [{"spam": [{"@value": "bacon"}]}]

    def test_container_add_context(self):
        cont = ld_container([{"spam": [{"@value": "bacon"}]}])
        cont.add_context([self.url])

        assert cont.context == [self.url]
        assert cont.full_context == [self.url]

    def test_container_parent(self):
        cont_data = [{"spam": [{"@value": "bacon"}]}]
        cont_parent = ld_container([{"ham": cont_data}])
        cont = ld_container(cont_data, parent=cont_parent, key="ham")
        assert cont.full_context == []

        cont_parent.add_context([self.url])

        assert cont.parent == cont_parent
        assert cont.full_context == [self.url]

    def test_container_full_context_and_path(self, httpserver):
        httpserver.expect_request("/url2").respond_with_json({"spam": "eggs"})
        httpserver.expect_request("/url3").respond_with_json({"ham": "bacon"})
        httpserver.expect_request("/url4").respond_with_json({"@context": {"id": "@id"}})

        cont_data = [{"spam": [{"@value": "bacon"}]}]
        cont_parent_data = [cont_data]
        cont_grand_parent = ld_container([{"ham": cont_parent_data}], context=[self.url])
        cont_parent = ld_container(cont_parent_data, context=[httpserver.url_for("/url2"),
                                                              httpserver.url_for("/url4")],
                                   parent=cont_grand_parent, key="ham")
        cont = ld_container(cont_data, context=[httpserver.url_for("/url3")], parent=cont_parent,
                            index=0)
        assert cont_parent.full_context == [self.url, httpserver.url_for("/url2"), httpserver.url_for("/url4")]
        assert cont.full_context == [self.url, httpserver.url_for("/url2"), httpserver.url_for("/url4"),
                                     httpserver.url_for("/url3")]
        assert cont_grand_parent.path == ["$"]
        assert cont_parent.path == ["$", "ham"]
        assert cont.path == ["$", "ham", 0]

    def test_container_str_and_repr(self):
        cont = ld_container([{"spam": [{"@value": "bacon"}]}])
        assert repr(cont) == "ld_container([{'spam': [{'@value': 'bacon'}]}])"
        with pytest.raises(NotImplementedError):
            str(cont)

    def test_to_python_id(self, mock_context):
        cont = ld_container([{}], context=[mock_context])
        assert cont._to_python("@id", "http://spam.eggs/ham") == "http://spam.eggs/ham"

    def test_to_python_id_with_prefix(self, mock_context):
        cont = ld_container([{}], context=[mock_context, {"prefix": self.url}])
        assert cont._to_python("@id", f"{self.url}identifier") == "prefix:identifier"

    def test_to_python_type(self, mock_context):
        cont = ld_dict([{"@type": ["@id"]}], context=[mock_context])
        assert cont._to_python("@type", ["@id"]) == ['@id']
        cont = ld_dict([{"@type": ["@id", "http://spam.eggs/Egg"]}], context=[mock_context])
        assert cont._to_python("@type", ["@id", "http://spam.eggs/Egg"]) == ["@id", "Egg"]

    def test_to_python_id_value(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_python("http://spam.eggs/ham",
                               [{"@id": "http://spam.eggs/spam"}]) == [{"@id": "http://spam.eggs/spam"}]
        assert cont._to_python("http://spam.eggs/ham",
                               {"@id": "http://spam.eggs/identifier"}) == "http://spam.eggs/identifier"

    def test_to_python_basic_value(self, mock_context):
        cont = ld_container([{}], context=[mock_context])
        assert cont._to_python("http://soam.eggs/spam", {"@value": "bacon"}) == 'bacon'
        assert cont._to_python("http://spam.eggs/spam", {"@value": True}) is True
        assert cont._to_python("http://spam.eggs/spam", {"@value": 123}) == 123

    def test_to_python_datetime_value(self, mock_context):
        cont = ld_container([{}], context=[mock_context])
        assert cont._to_python("http://spam.eggs/eggs", {
            "@value": "2022-02-22T00:00:00", "@type": "https://schema.org/DateTime"
        }) == "2022-02-22T00:00:00"  # TODO: #434 typed date is returned as string instead of date

    def test_to_python_error(self, mock_context):
        cont = ld_container([{}], context=[mock_context])
        with pytest.raises(TypeError):
            cont._to_python("http://spam.eggs/eggs", set())

    def test_to_expanded_id(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"@id": f"{self.url}identifier"}) == {"@id": f"{self.url}identifier"}

        # Regression test: "ham" is vocabulary and must not be expanded.
        assert cont._to_expanded_json({"@id": "ham"}) == {"@id": "ham"}

    def test_to_expanded_id_with_prefix(self, mock_context):
        cont = ld_dict([{}], context=[mock_context, {"prefix": self.url}])
        assert cont._to_expanded_json({"@id": "prefix:identifier"}) == {"@id": f"{self.url}identifier"}

        # Regression test: "ham" should still not be expaned, but "prefix:ham" should be.
        assert cont._to_expanded_json({"@id": "ham"}) == {"@id": "ham"}
        assert cont._to_expanded_json({"@id": "prefix:ham"}) == {"@id": f"{self.url}ham"}

    def test_to_expanded_type(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"@type": "Egg"}) == {"@type": ["http://spam.eggs/Egg"]}
        assert cont._to_expanded_json({"@type": ["Egg", "@id"]}) == {"@type": ["http://spam.eggs/Egg", "@id"]}

    def test_to_expanded_id_value(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"ham": "spam"}) == {"http://spam.eggs/ham": [{"@id": "spam"}]}

    def test_to_expanded_basic_value(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"spam": "bacon"}) == {"http://spam.eggs/spam": [{"@value": "bacon"}]}
        assert cont._to_expanded_json({"spam": 123}) == {"http://spam.eggs/spam": [{"@value": 123}]}
        assert cont._to_expanded_json({"spam": True}) == {"http://spam.eggs/spam": [{"@value": True}]}

    def test_to_expanded_datetime_value(self, mock_context):
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"eggs": datetime(2022, 2, 22)}) == {"http://spam.eggs/eggs": [{"@list": [
            {"@value": "2022-02-22T00:00:00", "@type": "https://schema.org/DateTime"}
        ]}]}
        cont = ld_dict([{}], context=[mock_context])
        assert cont._to_expanded_json({"eggs": time(5, 4, 3)}) == {"http://spam.eggs/eggs": [{"@list": [
            {"@value": "05:04:03", "@type": "https://schema.org/Time"}
        ]}]}

    def test_compact(self, mock_context):
        cont = ld_container([{"http://spam.eggs/eggs": [{"@list": [{"@value": "a"}]}],
                              "http://spam.eggs/spam": [{"@value": "bacon"}]}])
        assert cont.compact([mock_context]) == {"@context": mock_context, "spam": "bacon", "eggs": ["a"]}

    def test_is_ld_id(self):
        assert ld_container.is_ld_id([{"@id": "foo"}])
        assert not ld_container.is_ld_id([{"@id": "foo", "bar": "barfoo"}])
        assert not ld_container.is_ld_id({"@id": "foo"})
        assert not ld_container.is_ld_id([{"bar": "foo"}])

    def test_is_ld_value(self):
        assert ld_container.is_ld_value([{"@value": "foo"}])
        assert ld_container.is_ld_value([{"@value": "foo", "bar": "barfoo"}])
        assert not ld_container.is_ld_value({"@value": "foo"})
        assert not ld_container.is_ld_value([{"bar": "foo"}])

    def test_is_typed_ld_value(self):
        assert ld_container.is_typed_ld_value([{"@value": "foo", "@type": "bar"}])
        assert ld_container.is_typed_ld_value([{"@value": "foo", "@type": "bar", "bar": "barfoo"}])
        assert not ld_container.is_typed_ld_value([{"@type": "bar"}])
        assert not ld_container.is_typed_ld_value([{"@value": "foo"}])
        assert not ld_container.is_typed_ld_value({"@value": "foo", "@type": "bar"})
        assert not ld_container.is_typed_ld_value([{"bar": "foo"}])

    def test_are_values_equal(self):
        assert ld_container.are_values_equal({"@id": "foo"}, {"@id": "foo"})
        assert not ld_container.are_values_equal({"@id": "foo"}, {"@id": "bar"})
        assert ld_container.are_values_equal({"@id": "foo"}, {"@id": "foo", "@value": "bar"})
        assert ld_container.are_values_equal({"@value": "foo"}, {"@value": "foo"})
        assert ld_container.are_values_equal({"@value": "bar"}, {"@id": "foo", "@value": "bar"})
        assert not ld_container.are_values_equal({"@value": "foo"}, {"@value": "bar"})
        assert not ld_container.are_values_equal({"@type": "bar", "@value": "foo"}, {"@value": "foo"})
        assert ld_container.are_values_equal({"@type": "bar", "@value": "foo"}, {"@type": "bar", "@value": "foo"})
