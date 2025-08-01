# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pytest

pytest.skip("FIXME: Re-enable test after data model refactoring is done.", allow_module_level=True)

from hermes.commands import cli


def test_hermes_full():
    with pytest.raises(SystemExit) as se:
        cli.main()
        assert "choose from" in se


def test_hermes_harvest(hermes_env):
    hermes_env['hermes.toml'] = ""

    with hermes_env:
        result = hermes_env.run("harvest")

    assert result.returncode == 0


def test_hermes_process(hermes_env):
    hermes_env['hermes.toml'] = ""
    hermes_env['.hermes/harvest/test.json'] = ""

    with hermes_env:
        result = hermes_env.run("process")
        print(result.stdout.read())

    assert result.returncode == 0
