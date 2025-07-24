# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0
import re

# SPDX-FileContributor: Sophie Kernchen

import pytest, requests
from hermes.model.types.ld_container import ld_container

'''we expect user of this class to give the right input data types

example extended json ld:
        {
      "http://schema.org/name": [{"@value": "bacon"}],
      "eggs": [{"@id": "spam"}],
      "green": [{"@id": "png"}]
        }
'''


class TestLdContainer:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup_class(cls, httpserver):
        content = {
            "@context": {"type": "@type", "id": "@id", "schema": "http://schema.org/", "ham": "https://fake.site/",
                         "Organization": {"@id": "schema:Organization"}}}

        cls.url = httpserver.url_for("/url")

        httpserver.expect_request("/url").respond_with_json(content)

    def test_container_basic(self):
        cont = ld_container({"spam": [{"@value": "bacon"}]})

        assert cont.key is None
        assert cont.context == []
        assert cont._data == {"spam": [{"@value": "bacon"}]}
        assert cont.path == ["$"]

    def test_container_ld_value(self):
        cont = ld_container({"spam": [{"@value": "bacon"}]})

        assert cont.ld_value == {"spam": [{"@value": "bacon"}]}

    def test_container_add_context(self):

        cont = ld_container({"spam": [{"@value": "bacon"}]})
        cont.add_context([self.url])

        assert cont.context == [self.url]
        assert cont.full_context == [self.url]

    def test_container_parent(self):
        cont_parent = ld_container({"ham": [{"@value": "eggs"}]})
        cont = ld_container({"spam": [{"@value": "bacon"}]}, parent=cont_parent)
        assert cont.full_context == []

        cont_parent.add_context([self.url])

        assert cont.parent == cont_parent
        assert cont.full_context == [self.url]

    def test_container_full_context_and_path(self, httpserver):
        httpserver.expect_request("/url2").respond_with_json({"spam": "eggs"})
        httpserver.expect_request("/url3").respond_with_json({"ham": "bacon"})
        httpserver.expect_request("/url4").respond_with_json({"@context": {"id": "@id"}})

        cont_grand_parent = ld_container({"ham": [{"@value": "eggs"}]}, context=[self.url], index=1)
        cont_parent = ld_container({"ham": [{"@value": "eggs"}]}, context=[httpserver.url_for("/url2"),
                                                                           httpserver.url_for("/url4")],
                                   parent=cont_grand_parent)
        cont = ld_container({"spam": [{"@value": "bacon"}]}, context=[httpserver.url_for("/url3")], parent=cont_parent,
                            index=3)
        assert cont_parent.full_context == [self.url, httpserver.url_for("/url2"), httpserver.url_for("/url4")]
        assert cont.full_context == [self.url, httpserver.url_for("/url2"), httpserver.url_for("/url4"),
                                     httpserver.url_for("/url3")]
        assert cont_grand_parent.path == ["$"]          # FIXME: #381 Decision if the path should look like this
        assert cont_parent.path == ["$", None]
        assert cont.path == ["$", None, 3]

    def test_container_str_and_repr(self):
        cont = ld_container({"spam": [{"@value": "bacon"}]}, index=3)
        assert repr(cont) == ld_container({"spam": [{"@value": "bacon"}]}) #FIXME: #397 KeyError
        with pytest.raises(NotImplementedError):
            str(cont)

