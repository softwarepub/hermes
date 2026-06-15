# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import sys

import pytest

from hermes.commands import cli
from hermes.model import hermes_cache, SoftwareMetadata


@pytest.mark.parametrize(
    "cff, res",
    [
        (
            """cff-version: 1.2.0
title: Temp\nmessage: >-
  If you use this software, please cite it using the
  metadata from this file.
type: software
authors:
  - given-names: Max
    family-names: Mustermann
    email: max@muster.mann""",
            SoftwareMetadata({
                "@type": "SoftwareSourceCode",
                "author": {
                    "@list": [{
                        "@type": "Person",
                        "email": ["max@muster.mann"],
                        "familyName": ["Mustermann"],
                        "givenName": ["Max"]
                    }]
                },
                "name": ["Temp"]
            })
        ),
        (
            """# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf
#
# SPDX-License-Identifier: CC0-1.0

# SPDX-FileContributor: Michael Meinel

cff-version: 1.2.0
title: hermes
message: >-
  If you use this software, please cite it using the
  metadata from this file.
version: 0.9.0
license: "Apache-2.0"
abstract: "Tool to automate software publication. Not stable yet."
type: software
authors:
  - given-names: Michael
    family-names: Meinel
    email: michael.meinel@dlr.de
    affiliation: German Aerospace Center (DLR)
    orcid: "https://orcid.org/0000-0001-6372-3853"
  - given-names: Stephan
    family-names: Druskat
    email: stephan.druskat@dlr.de
    affiliation: German Aerospace Center (DLR)
    orcid: "https://orcid.org/0000-0003-4925-7248"
identifiers:
  - type: doi
    value: 10.5281/zenodo.13221384
    description: Version 0.8.1b1
""",
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/author": [
                    {
                        "@list": [
                            {
                                "@id": "https://orcid.org/0000-0001-6372-3853",
                                "@type": ["http://schema.org/Person"],
                                "http://schema.org/affiliation": [
                                    {
                                        "@type": ["http://schema.org/Organization"],
                                        "http://schema.org/name": [{"@value": "German Aerospace Center (DLR)"}]
                                    }
                                ],
                                "http://schema.org/email": [{"@value": "michael.meinel@dlr.de"}],
                                "http://schema.org/familyName": [{"@value": "Meinel"}],
                                "http://schema.org/givenName": [{"@value": "Michael"}]
                            },
                            {
                                "@id": "https://orcid.org/0000-0003-4925-7248",
                                "@type": ["http://schema.org/Person"],
                                "http://schema.org/affiliation": [
                                    {
                                        "@type": ["http://schema.org/Organization"],
                                        "http://schema.org/name": [{"@value": "German Aerospace Center (DLR)"}]
                                    }
                                ],
                                "http://schema.org/email": [{"@value": "stephan.druskat@dlr.de"}],
                                "http://schema.org/familyName": [{"@value": "Druskat"}],
                                "http://schema.org/givenName": [{"@value": "Stephan"}]
                            }
                        ]
                    }
                ],
                "http://schema.org/description": [{"@value": "Tool to automate software publication. Not stable yet."}],
                "http://schema.org/identifier": [{"@id": "https://doi.org/10.5281/zenodo.13221384"}],
                "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                "http://schema.org/name": [{"@value": "hermes"}],
                "http://schema.org/version": [{"@value": "0.9.0"}]
            })
        )
    ]
)
def test_cff_harvest(tmp_path, monkeypatch, cff, res):
    monkeypatch.chdir(tmp_path)
    cff_file = tmp_path / "CITATION.cff"
    cff_file.write_text(cff)

    config_file = tmp_path / "hermes.toml"
    config_file.write_text("[harvest]\nsources = [ \"cff\" ]")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "harvest", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(hermes_cache.HermesCacheManager.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager = hermes_cache.HermesCacheManager()
        manager.prepare_step("harvest")
        result = SoftwareMetadata.load_from_cache(manager, "cff")
        manager.finalize_step("harvest")
        sys.argv = orig_argv

    assert result == res


@pytest.mark.xfail
@pytest.mark.parametrize(
    "cff, res",
    [
        (
            """cff-version: 1.2.0
title: Test
message: None
type: software
authors:
  - given-names: Test
    family-names: Testi
    email: test.testi@test.testi
    affiliation: German Aerospace Center (DLR)
identifiers:
  - type: url
    value: "https://arxiv.org/abs/2201.09015"
  - type: doi
    value: 10.5281/zenodo.13221384
repository-code: "https://github.com/softwarepub/hermes"
abstract: for testing
url: "https://docs.software-metadata.pub/en/latest"
keywords:
  - testing
  - more testing
license: Apache-2.0
version: 9.0.1
date-released: "2026-01-16" """,
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/author": [
                    {
                        "@list": [
                            {
                                "@type": ["http://schema.org/Person"],
                                "http://schema.org/affiliation": [
                                    {
                                        "@type": ["http://schema.org/Organization"],
                                        "http://schema.org/name": [{"@value": "German Aerospace Center (DLR)"}]
                                    }
                                ],
                                "http://schema.org/email": [{"@value": "test.testi@test.testi"}],
                                "http://schema.org/familyName": [{"@value": "Testi"}],
                                "http://schema.org/givenName": [{"@value": "Test"}]
                            }
                        ]
                    }
                ],
                "http://schema.org/codeRepository": [{"@id": "https://github.com/softwarepub/hermes"}],
                "http://schema.org/datePublished": [{"@type": "http://schema.org/Date", "@value": "2026-01-16"}],
                "http://schema.org/description": [{"@value": "for testing"}],
                "http://schema.org/identifier": [{"@id": "https://doi.org/10.5281/zenodo.13221384"}],
                "http://schema.org/keywords": [{"@value": "testing"}, {"@value": "more testing"}],
                "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                "http://schema.org/name": [{"@value": "Test"}],
                "http://schema.org/url": [
                    {"@id": "https://arxiv.org/abs/2201.09015"},
                    {"@id": "https://docs.software-metadata.pub/en/latest"}
                ],
                "http://schema.org/version": [{"@value": "9.0.1"}]
            })
        )
    ]
)
def test_cff_harvest_multiple_urls(tmp_path, monkeypatch, cff, res):
    monkeypatch.chdir(tmp_path)
    cff_file = tmp_path / "CITATION.cff"
    cff_file.write_text(cff)

    config_file = tmp_path / "hermes.toml"
    config_file.write_text("[harvest]\nsources = [ \"cff\" ]")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "harvest", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(hermes_cache.HermesCacheManager.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager = hermes_cache.HermesCacheManager()
        manager.prepare_step("harvest")
        result = SoftwareMetadata.load_from_cache(manager, "cff")
        manager.finalize_step("harvest")
        sys.argv = orig_argv

    assert result == res
