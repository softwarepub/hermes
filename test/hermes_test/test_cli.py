# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pathlib
from unittest import mock
import pytest

from hermes import cli
from hermes.commands.deposit.error import DepositionUnauthorizedError
from hermes_test.mocks import mock_command


def test_hermes_full():
    runner = CliRunner()
    result = runner.invoke(cli.main)

    assert not result.exception


def test_hermes_harvest():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("harvest",))

    assert not result.exception


def test_hermes_process():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("process",))

    assert not result.exception


@pytest.mark.skip(
    reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options"
)
def test_hermes_with_deposit():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--deposit",))

    assert isinstance(result.exception, DepositionUnauthorizedError)


@pytest.mark.skip(
    reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options"
)
def test_hermes_with_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--postprocess",))

    assert not result.exception


def test_hermes_with_path():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--path", "./"))

    assert not result.exception


@pytest.mark.skip(
    reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options"
)
def test_hermes_with_deposit_and_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--deposit", "--postprocess"))

    assert isinstance(result.exception, DepositionUnauthorizedError)


@pytest.mark.skip(
    reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options"
)
def test_hermes_with_deposit_and_path():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--deposit", "--path", "./"))

    assert result.exit_code == 2


def test_hermes_with_path_and_postprocess():
    runner = CliRunner()
    result = runner.invoke(cli.main, args=("--path", "./", "--postprocess"))

    assert result.exit_code == 1


@pytest.mark.skip(
    reason="No clean way at the moment of adding more required options that are parsed by Click, \
                         e.g. files args or options"
)
def test_hermes_with_deposit_and_postprocess_and_path():
    runner = CliRunner()
    result = runner.invoke(
        cli.main, args=("--deposit", "--postprocess", "--path", "./")
    )

    assert isinstance(result.exception, DepositionUnauthorizedError)
