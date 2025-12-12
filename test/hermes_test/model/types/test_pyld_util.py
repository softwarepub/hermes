# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pytest

from unittest import mock

from pyld import jsonld
from hermes.model.types import pyld_util


@pytest.fixture
def ld_proc():
    return pyld_util.JsonLdProcessor()


def test_mock_document_compact(ld_proc, mock_document):
    compact_document = ld_proc.compact(mock_document.expanded(), [mock_document.vocabulary()], {})
    assert compact_document == mock_document.compact()


def test_mock_document_expanded(ld_proc, mock_document):
    expanded_document = ld_proc.expand(mock_document.compact(), {})
    assert expanded_document == mock_document.expanded()


def test_initial_context(ld_proc, httpserver, mock_document):
    with pytest.raises(jsonld.JsonLdError):
        active_ctx = ld_proc.initial_ctx(
            [{"s": "www.spam.de"}],
            {"documentLoader": pyld_util.bundled_loader}
        )
    url = httpserver.url_for("/")
    httpserver.expect_request("/").respond_with_json({"@context": mock_document.vocabulary(url)})
    active_ctx = ld_proc.initial_ctx(
        [url],
        {"documentLoader": pyld_util.bundled_loader}
    )
    assert "spam" in active_ctx["mappings"]
    assert active_ctx["mappings"]["spam"]["@id"] == url + "spam"
    assert active_ctx["mappings"]["ham"]["@id"] == url + "ham"
    assert active_ctx["mappings"]["use_until"]["@id"] == url + "use_until"
    assert active_ctx["mappings"]["Egg"]["@id"] == url + "Egg"
    assert active_ctx["processingMode"] == "json-ld-1.1"


def test_expand_iri(ld_proc, mock_context):
    active_ctx = {'processingMode': 'json-ld-1.1',
                  'mappings': mock_context}
    assert ld_proc.expand_iri(active_ctx, "spam") == "http://spam.eggs/" + "spam"


def test_compact_iri(ld_proc, mock_context):
    active_ctx = {'mappings': {'spam': {'reverse': False, 'protected': False, '_prefix': False,
                                        '_term_has_colon': False, '@id': 'http://spam.eggs/spam'},
                               'ham': {'reverse': False, 'protected': False, '_prefix': False,
                                       '_term_has_colon': False, '@id': 'http://spam.eggs/ham', '@type': '@id'},
                               },
                  'processingMode': 'json-ld-1.1', '_uuid': 'c641b9db-b0e8-11f0-bc68-9cfce89fd5b3'}

    assert ld_proc.compact_iri(active_ctx, "http://spam.eggs/spam") == "spam"
    assert ld_proc.compact_iri(active_ctx, "http://spam.eggs/bacon") == "http://spam.eggs/bacon"


def test_register_typemap():
    len_typemap = len(pyld_util.JsonLdProcessor._type_map)
    pyld_util.JsonLdProcessor.register_typemap("function", **dict(spam="hallo"))
    assert len(pyld_util.JsonLdProcessor._type_map) == len_typemap + 1
    assert pyld_util.JsonLdProcessor._type_map["spam"] == [("function", "hallo")]


def test_apply_typemap():
    pyld_util.JsonLdProcessor._type_map["spam"] = [(lambda c: isinstance(c, list), lambda c, **_: c[0]+"eggs")]
    ld_value, ld_output = pyld_util.JsonLdProcessor.apply_typemap(["ham"], "spam")
    assert ld_output == "spam"
    assert ld_value == "hameggs"
    ld_value, ld_output = pyld_util.JsonLdProcessor.apply_typemap(["eggs", "ham"], "spam")
    assert ld_output == "spam"
    assert ld_value == "eggseggs"
    ld_value, ld_output = pyld_util.JsonLdProcessor.apply_typemap("ham", "spam")
    assert ld_value == "ham"
