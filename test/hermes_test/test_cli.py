# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pathlib
from unittest import mock
import pytest

import click
from click.testing import CliRunner

from hermes import cli
from hermes.commands.deposit.error import DepositionUnauthorizedError
from hermes_test.mocks import mock_command


def test_workflow_setup():
    wf = cli.WorkflowCommand()

    wf.add_command(mock_command("spam")[1])
    wf.add_command(mock_command("eggs")[1])

    ctx = click.Context(wf)
    assert wf.list_commands(ctx) == ["spam", "eggs"]


def test_workflow_no_dupes():
    wf = cli.WorkflowCommand()

    wf.add_command(mock_command("spam")[1])
    wf.add_command(mock_command("eggs")[1])
    wf.add_command(mock_command("ham")[1], "spam")

    ctx = click.Context(wf)
    assert wf.list_commands(ctx) == ["spam", "eggs"]
    assert wf.get_command(ctx, "spam").name == "ham"


def test_workflow_invoke():
    wf = cli.WorkflowCommand()
    spam, spam_cmd = mock_command("spam")
    eggs, eggs_cmd = mock_command("eggs")

    wf.add_command(spam_cmd)
    wf.add_command(eggs_cmd)

    ctx = click.Context(wf)
    ctx.params['path'] = pathlib.Path.cwd()
    ctx.params['config'] = pathlib.Path.cwd() / 'hermes.toml'
    wf.invoke(ctx)

    spam.assert_called_once()
    eggs.assert_called_once()


def test_workflow_invoke_with_cb():
    wf = cli.WorkflowCommand()
    cb_mock = mock.Mock()
    spam, spam_cmd = mock_command("spam")
    eggs, eggs_cmd = mock_command("eggs")

    wf.add_command(spam_cmd)
    wf.add_command(eggs_cmd)
    wf.result_callback()(cb_mock)

    ctx = click.Context(wf)
    ctx.params['path'] = pathlib.Path.cwd()
    ctx.params['config'] = pathlib.Path.cwd() / 'hermes.toml'
    wf.invoke(ctx)

    spam.assert_called_once()
    eggs.assert_called_once()
    cb_mock.assert_called_with(["spam", "eggs"], config=ctx.params['config'], path=ctx.params['path'])


def test_hermes_full():
    runner = CliRunner()
    result = runner.invoke(cli.main)

    assert not result.exception


def test_hermes_harvest():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('harvest', ))

    assert not result.exception


def test_hermes_process():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('process',))

    assert not result.exception


@pytest.mark.skip(reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options")
def test_hermes_with_deposit():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--deposit', ))

    assert isinstance(result.exception, DepositionUnauthorizedError)


@pytest.mark.skip(reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options")
def test_hermes_with_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--postprocess', ))

    assert not result.exception


def test_hermes_with_path():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--path', './'))

    assert not result.exception


@pytest.mark.skip(reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options")
def test_hermes_with_deposit_and_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--deposit', '--postprocess'))

    assert isinstance(result.exception, DepositionUnauthorizedError)


@pytest.mark.skip(reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options")
def test_hermes_with_deposit_and_path():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--deposit', '--path', './'))

    assert result.exit_code == 2


def test_hermes_with_path_and_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--path', './', '--postprocess'))

    assert result.exit_code == 1


@pytest.mark.skip(reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options")
def test_hermes_with_deposit_and_postprocess_and_path():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=('--deposit', '--postprocess', '--path', './'))

    assert isinstance(result.exception, DepositionUnauthorizedError)
