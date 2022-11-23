# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from importlib.metadata import EntryPoint

import pytest

from hermes.model.context import HermesContext, HermesHarvestContext


@pytest.fixture
def harvest_ctx(request: pytest.FixtureRequest):
    ctx = HermesContext()
    return HermesHarvestContext(ctx, EntryPoint(name=request.function, group='hermes.harvest', value='hermes_test:hctx'))


def test_context_default(harvest_ctx):
    harvest_ctx.update('spam', 'eggs', test=True)

    assert harvest_ctx._data['spam'] == [['eggs', {'test': True}]]


def test_context_update_append(harvest_ctx):
    harvest_ctx.update('spam', 'noodles', index=0)
    harvest_ctx.update('spam', 'eggs', index=1)

    assert harvest_ctx._data['spam'] == [['noodles', {'index': 0}], ['eggs', {'index': 1}]]


def test_context_update_replace(harvest_ctx):
    harvest_ctx.update('spam', 'noodles', test=True)
    harvest_ctx.update('spam', 'eggs', test=True)

    assert harvest_ctx._data['spam'] == [['eggs', {'test': True}]]


def test_context_bulk_flat(harvest_ctx):
    harvest_ctx.update_from({
        'ans': 42,
        'spam': 'eggs'
    }, test=True)

    assert harvest_ctx._data['ans'] == [[42, {'test': True}]]
    assert harvest_ctx._data['spam'] == [['eggs', {'test': True}]]


def test_context_bulk_complex(harvest_ctx):
    harvest_ctx.update_from({
        'ans': 42,
        'author': [
            {'name': 'Monty Python', 'email': 'eggs@spam.io'},
            {'name': 'Herr Mes'},
        ]
    }, test=True)

    assert harvest_ctx._data['ans'] == [[42, {'test': True}]]
    assert harvest_ctx._data['author[0].name'] == [['Monty Python', {'test': True}]]
    assert harvest_ctx._data['author[0].email'] == [['eggs@spam.io', {'test': True}]]
    assert harvest_ctx._data['author[1].name'] == [['Herr Mes', {'test': True}]]


def test_context_bulk_replace(harvest_ctx):
    harvest_ctx.update('author[0].name', 'Monty Python', test=True)
    harvest_ctx.update_from({'author': [{'name': 'Herr Mes', 'email': 'eggs@spam.io'}]}, test=True)

    assert harvest_ctx._data['author[0].name'] == [['Herr Mes', {'test': True}]]
    assert harvest_ctx._data['author[0].email'] == [['eggs@spam.io', {'test': True}]]


def test_context_bulk_append(harvest_ctx):
    harvest_ctx.update('author[0].name', 'Monty Python', index=0)
    harvest_ctx.update_from({'author': [{'name': 'Herr Mes', 'email': 'eggs@spam.io'}]}, index=1)

    assert harvest_ctx._data['author[0].name'] == [['Monty Python', {'index': 0}], ['Herr Mes', {'index': 1}]]
    assert harvest_ctx._data['author[0].email'] == [['eggs@spam.io', {'index': 1}]]
