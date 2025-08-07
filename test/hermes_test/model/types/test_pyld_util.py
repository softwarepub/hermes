# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Michael Meinel
#
# SPDX-License-Identifier: Apache-2.0

import pytest

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
