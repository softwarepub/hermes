# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat

from importlib.metadata import EntryPoint

import pytest
from pytest import FixtureRequest

import hermes.commands.process.git as process
from hermes.model.context import HermesContext, HermesHarvestContext, CodeMetaContext


@pytest.fixture
def _data():
    return {
        'contributor': [
            {
                '@type': 'Person',
                'name': 'Git Author',
                'email': 'f@mail.com',
                'contributionRole': [
                    {
                        '@type': 'Role',
                        'roleName': 'git author',
                        'startTime': '2023-01-13T08:57:12+01:00',
                        'endTime': '2023-01-13T08:57:12+01:00'
                    }
                ]
            },
            {
                '@type': 'Person',
                'name': 'Git Committer',
                'email': 'c@mail.com',
                'contributionRole': [
                    {
                        '@type': 'Role',
                        'roleName': 'git committer',
                        'startTime': '2023-01-13T08:57:12+01:00',
                        'endTime': '2023-01-13T08:57:12+01:00'
                    }
                ]
            }
        ],
        'hermes:gitBranch': 'test-branch'
    }


@pytest.fixture
def harvest_ctx(request: FixtureRequest, _data):
    _ctx = HermesContext()
    harvest_ctx = HermesHarvestContext(
        _ctx,
        EntryPoint(name=request.function.__name__, group='hermes.harvest', value='hermes_test:ctx')
    )
    harvest_ctx.update_from(_data)
    return harvest_ctx


def test_process_git(harvest_ctx, _data):
    ctx = CodeMetaContext()
    assert ctx.get_data() == {}
    process.process(ctx, harvest_ctx)
    assert ctx.get_data() == _data


def test_process_git_empties_harvesting_context(harvest_ctx):
    ctx = CodeMetaContext()
    process.process(ctx, harvest_ctx)
    assert harvest_ctx.get_data() == {}
