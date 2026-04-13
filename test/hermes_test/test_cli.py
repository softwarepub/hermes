# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

# flake8: noqa

import pytest
import os

from hermes.commands import cli
from hermes import error


def test_hermes_full():
    with pytest.raises(SystemExit) as se:
        cli.main()
        assert "choose from" in se


def test_hermes_harvest(hermes_env):
    hermes_env['hermes.toml'] = "[harvest]\nsources = [\"cff\", \"foo\"]\n"
    hermes_env['CITATION.cff'] = """cff-version: 1.2.0
title: Test
message: >-
  test tests
type: software
authors:
  - given-names: Testi"""

    with hermes_env:
        result = hermes_env.run("harvest")
        stdout_res = result.stdout.read().decode()

        test_dir = hermes_env.test_path
        assert len(os.listdir(test_dir)) == 4
        log = test_dir / "hermes.log"
        #print(log.read_text())
        assert log.exists()
        assert len(os.listdir(test_dir/ ".hermes/harvest/cff/")) == 3
        output_file = test_dir / ".hermes/harvest/cff/codemeta.json"
        assert output_file.exists()
    assert result.returncode == 0
    assert "Run cff plugin" in stdout_res
    assert "Plugin foo not found" in stdout_res


@pytest.mark.dev
def test_hermes_harvest_no_plugin(hermes_env):
    hermes_env['hermes.toml'] = "[harvest]\nsources = []\n"
    with hermes_env:
        result = hermes_env.run("harvest")
        stdout_res = result.stdout.read().decode()
        test_dir = hermes_env.test_path
        log = test_dir / "hermes.log"

    assert result.returncode == 1
    assert "hermes.error.MisconfigurationError: No harvest plugin was configured to be run and loaded." in stdout_res


def test_hermes_process(hermes_env):
    hermes_env['hermes.toml'] = "[process]\nsources = [\"cff\"]"
    hermes_env['.hermes/harvest/cff/codemeta.json'] = "{}"

    with hermes_env:
        result = hermes_env.run("process")

    assert result.returncode == 0
