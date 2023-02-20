# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0
#
# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import pathlib

import click
import pytest

from hermes.commands.harvest import util
from hermes_test.mocks import mock_command


@pytest.fixture()
def click_ctx():
    spam, spam_cmd = mock_command('spam')
    parent = click.Context(spam_cmd)
    parent.params['path'] = pathlib.Path('foobar')
    ctx = click.Context(spam_cmd, parent=parent)
    return ctx


@pytest.fixture()
def click_ctx_no_parent():
    spam, spam_cmd = mock_command('spam')
    ctx = click.Context(spam_cmd)
    return ctx


def test_get_project_path(click_ctx):
    path = util.get_project_path(click_ctx)
    assert isinstance(path, pathlib.Path)
    assert path == pathlib.Path('foobar')


def test_get_project_path_exception(click_ctx_no_parent):
    with pytest.raises(RuntimeError) as e:
        util.get_project_path(click_ctx_no_parent)
    assert str(e.value) == 'No parent context!'
