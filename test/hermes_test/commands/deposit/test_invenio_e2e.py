# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from datetime import date
import sys

import pytest

from hermes.commands import cli
from hermes.model import hermes_cache
from hermes.model.api import SoftwareMetadata


@pytest.fixture
def sandbox_auth(pytestconfig):
    if pytestconfig.getoption("sandbox_auth"):
        yield pytestconfig.getoption("sandbox_auth")
    else:
        pytest.skip("No auth token was supplied. Hint: Supply it with --sandbox_auth your_token")


@pytest.mark.parametrize(
    "metadata, invenio_metadata",
    [
        (
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/description": [{"@value": "for testing"}],
                "http://schema.org/name": [{"@value": "Test"}],
                "http://schema.org/author": [{
                    "@type": "http://schema.org/Person",
                    "http://schema.org/familyName": [{"@value": "Test"}],
                    "http://schema.org/givenName": [{"@value": "Testi"}]
                }],
                "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}]
            }),
            {
                "upload_type": "software",
                "publication_date": date.today().isoformat(),
                "title": "Test",
                "creators": [{"name": "Test, Testi"}],
                "description": "for testing",
                "access_right": "closed",
                "license": "apache-2.0",
                "prereserve_doi": True,
                "related_identifiers": [
                    {"identifier": "10.5281/zenodo.13221383", "relation": "isCompiledBy", "scheme": "doi"}
                ]
            }
        )
    ]
)
def test_invenio_deposit(tmp_path, monkeypatch, sandbox_auth, metadata, invenio_metadata):
    monkeypatch.chdir(tmp_path)

    manager = hermes_cache.HermesCacheManager(tmp_path)
    manager.prepare_step("curate")
    with manager["result"] as cache:
        cache["codemeta"] = metadata.compact()
    manager.finalize_step("curate")

    (tmp_path / "test.txt").write_text("Test, oh wonderful test!\n")

    config_file = tmp_path / "hermes.toml"
    config_file.write_text(f"""[deposit]
target = "invenio"
[deposit.invenio]
site_url = "https://sandbox.zenodo.org"
access_right = "closed"
auth_token = "{sandbox_auth}"
files = ["test.txt"]
[deposit.invenio.api_paths]
licenses = "api/vocabularies/licenses"
""")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "deposit", "--path", str(tmp_path), "--config", str(config_file), "--initial"]
    result = {}
    try:
        monkeypatch.setattr(hermes_cache.HermesCacheManager.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager.prepare_step("deposit")
        with manager["invenio"] as cache:
            result = cache["deposit"]
        manager.finalize_step("deposit")
        sys.argv = orig_argv

    assert result == invenio_metadata
