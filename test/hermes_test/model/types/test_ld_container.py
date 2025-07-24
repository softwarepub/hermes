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


def test_container_basic():
    cont = ld_container({"spam": [{"@value": "bacon"}]})

    assert cont.key is None
    assert cont.context == []
    assert cont._data == {"spam": [{"@value": "bacon"}]}


def test_container_ld_value():
    cont = ld_container({"spam": [{"@value": "bacon"}]})

    assert cont.ld_value == {"spam": [{"@value": "bacon"}]}


def test_container_add_context(httpserver):
    content = {"@context": {"type": "@type", "id": "@id", "schema": "http://schema.org/", "ham": "https://fake.site/",
                            "Organization": {"@id": "schema:Organization"}}}

    url = httpserver.url_for("/url")

    httpserver.expect_request("/url").respond_with_json(content)
    cont = ld_container({"spam": [{"@value": "bacon"}]})
    cont.add_context([url])

    assert cont.context == [url]
    assert cont.full_context == [url]


def test_container_parent(httpserver):
    content = {"@context": {"type": "@type", "id": "@id", "schema": "http://schema.org/", "ham": "https://fake.site/",
                            "Organization": {"@id": "schema:Organization"}}}

    url = httpserver.url_for("/url")

    httpserver.expect_request("/url").respond_with_json(content)

    cont_parent = ld_container({"ham": [{"@value": "eggs"}]})
    cont = ld_container({"spam": [{"@value": "bacon"}]}, parent=cont_parent)
    assert cont.full_context == []

    cont_parent.add_context([url])

    assert cont.parent == cont_parent
    assert cont.full_context == [url]
