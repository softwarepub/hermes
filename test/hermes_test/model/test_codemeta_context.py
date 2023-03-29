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


def test_merge_contexts_from(mock_ep):
    _self = CodeMetaContext()
    assert not _self.contexts
    other = HermesHarvestContext(None, mock_ep)
    context = ('foo', 'bar')
    other.contexts.add(context)
    _self.merge_contexts_from(other)
    assert _self.contexts == {context}
