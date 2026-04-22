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
        test_dir = hermes_env.test_path
        assert len(os.listdir(test_dir / ".hermes/process/result/")) == 3
        output_file = test_dir / ".hermes/process/result/codemeta.json"
        assert output_file.exists()

    assert result.returncode == 0


def test_hermes_curate(hermes_env, tmpdir):
    hermes_env['hermes.toml'] = "[curate]\nplugin = \"pass_curate\""
    hermes_env['.hermes/process/result/codemeta.json'] = "{\"@context\": [\"https://doi.org/10.5063/schema/codemeta-2.0\"], \"name\": \"hermes\", \"version\": \"0.9.0\"}"

    with hermes_env:
        result = hermes_env.run("curate")
        test_dir = hermes_env.test_path
        assert len(os.listdir(test_dir / ".hermes/curate/result/")) == 3
        output_file = test_dir / ".hermes/curate/result/codemeta.json"

        # One small change and it breaks, so maybe adapt it to a simpler includes test
        content = "{\"@context\": [\"https://doi.org/10.5063/schema/codemeta-2.0\", {\"schema\": " \
                  "\"http://schema.org/\", \"prov\": \"http://www.w3.org/ns/prov#\", \"hermes-rt\": " \
                  "\"https://schema.software-metadata.pub/hermes-runtime/1.0/\", \"hermes\": " \
                  "\"https://schema.software-metadata.pub/hermes-content/1.0/\"}], \"name\": \"hermes\"," \
                  " \"version\": \"0.9.0\"}"
        assert output_file.read_text() == content

    assert result.returncode == 0


def test_hermes_deposit(hermes_env):
    hermes_env['hermes.toml'] = "[deposit]\ntarget = \"file\""
    hermes_env['.hermes/curate/result/codemeta.json'] = "{}"

    with hermes_env:
        result = hermes_env.run("deposit")
        test_dir = hermes_env.test_path
        assert len(os.listdir(test_dir / ".hermes/deposit/file/")) == 2
        output_file = test_dir / "hermes.json"
        assert "@context" in output_file.read_text()

    assert result.returncode == 0


def test_hermes_postprocess(hermes_env):
    hermes_env['hermes.toml'] = "[postprocess]\nrun = [ \"config_invenio_rdm_record_id\"] \n" \
                                "[deposit.invenio_rdm]\ncommunities = []\n"
    hermes_env['.hermes/deposit/invenio_rdm/result.json'] = "{\"record_id\": 1234}"

    with hermes_env:
        result = hermes_env.run("postprocess")
        #log = hermes_env.test_path  / "hermes.log"
        #print(log.read_text())
        output_file = hermes_env.test_path / "hermes.toml"
        assert output_file.read_text() == "[postprocess]\nrun = [ \"config_invenio_rdm_record_id\"] \n" \
                                          "[deposit.invenio_rdm]\ncommunities = []\nrecord_id = 1234\n"

    assert result.returncode == 0
