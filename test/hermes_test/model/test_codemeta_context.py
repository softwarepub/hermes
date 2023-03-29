# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat

import pytest
from unittest.mock import Mock

from hermes.model.context import CodeMetaContext, HermesHarvestContext


@pytest.fixture
def mock_ep():
    ep = Mock()
    ep.name = 'mock_name'
    return ep


@pytest.fixture
def _context():
    return 'foo', 'bar'


@pytest.fixture
def _codemeta_context():
    return CodeMetaContext()


@pytest.fixture
def _data(_codemeta_context):
    return {
        '@context': 'https://doi.org/10.5063/schema/codemeta-2.0',
        '@type': 'SoftwareSourceCode'
    }


@pytest.fixture
def _data_with_contexts(_codemeta_context):
    return {
        '@type': 'SoftwareSourceCode',
        '@context': [
            'https://doi.org/10.5063/schema/codemeta-2.0',
            {'foo': 'bar'}
        ]
    }


def test_merge_contexts_from(mock_ep, _context, _codemeta_context):
    assert not _codemeta_context.contexts
    other = HermesHarvestContext(None, mock_ep)
    other.contexts.add(_context)
    _codemeta_context.merge_contexts_from(other)
    assert _codemeta_context.contexts == {_context}


def test_prepare_codemeta(_codemeta_context, _context, _data):
    assert not _codemeta_context.keys()
    _codemeta_context.prepare_codemeta()
    assert _codemeta_context.get_data() == _data


def test_prepare_codemeta_with_contexts(_codemeta_context, _context, _data_with_contexts):
    assert not _codemeta_context.keys()
    _codemeta_context.contexts = {_context}
    _codemeta_context.prepare_codemeta()
    assert _codemeta_context.get_data() == _data_with_contexts
