# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import json
import sys

import pytest

from hermes.commands import cli
from hermes.model import context_manager, SoftwareMetadata


@pytest.mark.parametrize(
    "metadata",
    [
        SoftwareMetadata({
            "@type": ["http://schema.org/SoftwareSourceCode"],
            "http://schema.org/description": [{"@value": "for testing"}],
            "http://schema.org/name": [{"@value": "Test"}]
        }),
    ]
)
def test_file_deposit(tmp_path, monkeypatch, metadata):
    monkeypatch.chdir(tmp_path)

    manager = context_manager.HermesContext(tmp_path)
    manager.prepare_step("curate")
    with manager["result"] as cache:
        cache["codemeta"] = metadata.compact()
    manager.finalize_step("curate")

    config_file = tmp_path / "hermes.toml"
    config_file.write_text("[deposit]\ntarget = \"file\"")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "deposit", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(context_manager.HermesContext.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        with open("hermes.json", "r") as cache:
            result = SoftwareMetadata(json.load(cache))
        sys.argv = orig_argv

    assert result == metadata
