# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat

import json
from importlib.metadata import EntryPoint

import pytest
from pytest import FixtureRequest
from unittest.mock import patch, Mock

import hermes.commands.harvest.git as harvest
from hermes.model.context import HermesContext, HermesHarvestContext


@pytest.fixture
def harvest_ctx(request: FixtureRequest):
    ctx = HermesContext()
    return HermesHarvestContext(
        ctx,
        EntryPoint(name=request.function.__name__, group='hermes.harvest', value='hermes_test:ctx')
    )


@pytest.fixture
def codemeta():
    return json.loads("""
{
  "contributor": [
    {
      "@type": "Person",
      "name": "Git Author + Committer",
      "email": "e@mail.com",
      "hermes:contributionRole": [
        {
          "@type": "Role",
          "roleName": "git author",
          "startTime": "2023-01-13T08:57:12+01:00",
          "endTime": "2023-01-13T08:57:12+01:00"
        },
        {
          "@type": "Role",
          "roleName": "git committer",
          "startTime": "2023-01-13T08:57:12+01:00",
          "endTime": "2023-01-13T08:57:12+01:00"
        }
      ]
    },
    {
      "@type": "Person",
      "name": "Git Author",
      "email": "f@mail.com",
      "hermes:contributionRole": [
        {
          "@type": "Role",
          "roleName": "git author",
          "startTime": "2023-01-13T08:57:12+01:00",
          "endTime": "2023-01-13T08:57:12+01:00"
        }
      ]
    },
    {
      "@type": "Person",
      "name": "Git Committer",
      "email": "g@mail.com",
      "hermes:contributionRole": [
        {
          "@type": "Role",
          "roleName": "git committer",
          "startTime": "2023-01-13T08:57:12+01:00",
          "endTime": "2023-01-13T08:57:12+01:00"
        }
      ]
    }
  ],
  "hermes:gitBranch": "test-branch"
}
    """)


@pytest.fixture
def git_log_output():
    return '''
Git Author + Committer|e@mail.com|2023-01-13T08:57:12+01:00|Git Author + Committer|e@mail.com|2023-01-13T08:57:12+01:00
Git Author|f@mail.com|2023-01-13T08:57:12+01:00|Git Committer|g@mail.com|2023-01-13T08:57:12+01:00
    '''


@pytest.fixture
def git_branch_output():
    return 'test-branch'


@pytest.fixture
def mock_click_ctx():
    ctx = Mock()
    ctx.parent = Mock(params={'path': '.'})
    return ctx


@patch("hermes.commands.harvest.git.subprocess.run")
def test_harvest_git(mock_run, mock_click_ctx, harvest_ctx, git_log_output, git_branch_output, codemeta):
    # Mocking the output of the subprocess call to git log to retrieve author and committer info
    mock_stdout = Mock()
    mock_stdout.configure_mock(
        **{
            "stdout.decode.return_value": git_log_output,
            "returncode": 0
        }
    )

    # Mocking the output of the subprocess call to git rev-parse to retrieve branch id
    mock_get_branch = Mock()
    mock_get_branch.configure_mock(
        **{
            "stdout.decode.return_value": git_branch_output,
            "returncode": 0
        }
    )

    # Define outputs from "running" the subprocess mock
    mock_run.side_effect = [mock_get_branch, mock_stdout]

    harvest.harvest_git(mock_click_ctx, harvest_ctx)

    result = harvest_ctx.get_data()
    assert result == codemeta
