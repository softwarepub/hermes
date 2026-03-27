# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

# flake8: noqa

import pytest

from hermes.commands import cli


def test_hermes_full():
    with pytest.raises(SystemExit) as se:
        cli.main()
        assert "choose from" in se


def test_hermes_harvest(hermes_env):
    hermes_env['hermes.toml'] = "[harvest]\nsources = [\"cff\"]\n"
    hermes_env['CITATION.cff'] = """cff-version: 1.2.0
title: Test
message: >-
  test tests
type: software
authors:
  - given-names: Testi"""

    with hermes_env:
        result = hermes_env.run("harvest")

    assert result.returncode == 0


def test_hermes_process(hermes_env):
    hermes_env['hermes.toml'] = "[process]\nsources = [\"cff\"]"
    hermes_env['.hermes/harvest/cff/codemeta.json'] = "{}"

    with hermes_env:
        result = hermes_env.run("process")

    assert result.returncode == 0
