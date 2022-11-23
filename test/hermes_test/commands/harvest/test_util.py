import pathlib

import click
import pytest

from hermes.commands.harvest import util
from hermes_test.mocks import mock_command


@pytest.fixture()
def click_ctx():
    spam, spam_cmd = mock_command('spam')
    parent = click.Context(spam_cmd)
    parent.params['path'] = pathlib.PosixPath('foobar')
    ctx = click.Context(spam_cmd, parent=parent)
    return ctx


def test_get_project_path(click_ctx):
    path = util.get_project_path(click_ctx)
    assert isinstance(path, pathlib.PosixPath)
    assert path == pathlib.PosixPath('foobar')

