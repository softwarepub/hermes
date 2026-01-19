# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import pytest
import sys
from hermes.model import context_manager, SoftwareMetadata
from hermes.commands import cli


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
        ),
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
                    {"@id": 'https://arxiv.org/abs/2201.09015'},
                    {"@id": "https://docs.software-metadata.pub/en/latest"}
                ],
                "http://schema.org/version": [{"@value": "9.0.1"}]
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
        monkeypatch.setattr(context_manager.HermesContext.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit:
        manager = context_manager.HermesContext()
        manager.prepare_step("harvest")
        with manager["cff"] as cache:
            result = SoftwareMetadata(cache["codemeta"])
        manager.finalize_step("harvest")
    finally:
        sys.argv = orig_argv

    # FIXME: update to compare the SoftwareMetadata objects instead of the data_dicts (in multiple places)
    # after merge with refactor/data-model and/or refactor/423-implement-public-api
    assert result.data_dict == res.data_dict


@pytest.mark.parametrize(
    "codemeta, res",
    [
        (
            """{
    "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
    "type": "SoftwareSourceCode",
    "description": "for testing",
    "name": "Test"
}""",
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/description": [{"@value": "for testing"}],
                "http://schema.org/name": [{"@value": "Test"}]
            })
        ),
        (
            """{
    "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
    "type": "SoftwareSourceCode",
    "applicationCategory": "Testing",
    "author": [
        {
            "id": "_:author_1",
            "type": "Person",
            "email": "test.testi@test.testi",
            "familyName": "Testi",
            "givenName": "Test"
        }
    ],
    "codeRepository": "https://github.com/softwarepub/hermes",
    "contributor": {
        "id": "_:contributor_1",
        "type": "Person",
        "email": "test.testi@test.testi",
        "familyName": "Testi",
        "givenName": "Test"
    },
    "dateCreated": "2026-01-16",
    "dateModified": "2026-01-16",
    "datePublished": "2026-01-16",
    "description": "for testing",
    "funder": {
        "type": "Organization",
        "name": "TestsTests"
    },
    "keywords": [
        "testing",
        "more testing"
    ],
    "license": [
        "https://spdx.org/licenses/Adobe-2006",
        "https://spdx.org/licenses/Abstyles",
        "https://spdx.org/licenses/AGPL-1.0-only"
    ],
    "name": "Test",
    "operatingSystem": "Windows",
    "programmingLanguage": [
        "Python",
        "Python 3"
    ],
    "relatedLink": "https://docs.software-metadata.pub/en/latest",
    "schema:releaseNotes": "get it now",
    "version": "1.1.1",
    "developmentStatus": "abandoned",
    "funding": "none :(",
    "codemeta:isSourceCodeOf": {
        "id": "HERMES"
    },
    "issueTracker": "https://github.com/softwarepub/hermes/issues",
    "referencePublication": "https://arxiv.org/abs/2201.09015"
}""",
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/applicationCategory": [{"@id": "Testing"}],
                "http://schema.org/author": [
                    {
                        "@list": [
                            {
                                "@id": "_:author_1",
                                "@type": ["http://schema.org/Person"],
                                "http://schema.org/email": [{"@value": "test.testi@test.testi"}],
                                "http://schema.org/familyName": [{"@value": "Testi"}],
                                "http://schema.org/givenName": [{"@value": "Test"}]
                            }
                        ]
                    }
                ],
                "http://schema.org/codeRepository": [{"@id": "https://github.com/softwarepub/hermes"}],
                "http://schema.org/contributor": [
                    {
                        "@id": "_:contributor_1",
                        "@type": ["http://schema.org/Person"],
                        "http://schema.org/email": [{"@value": "test.testi@test.testi"}],
                        "http://schema.org/familyName": [{"@value": "Testi"}],
                        "http://schema.org/givenName": [{"@value": "Test"}]
                    }
                ],
                "http://schema.org/dateCreated": [{"@type": "http://schema.org/Date", "@value": "2026-01-16"}],
                "http://schema.org/dateModified": [{"@type": "http://schema.org/Date", "@value": "2026-01-16"}],
                "http://schema.org/datePublished": [{"@type": "http://schema.org/Date", "@value": "2026-01-16"}],
                "http://schema.org/description": [{"@value": "for testing"}],
                "http://schema.org/funder": [
                    {
                        "@type": ["http://schema.org/Organization"],
                        "http://schema.org/name": [{"@value": "TestsTests"}]
                    }
                ],
                "http://schema.org/keywords": [{"@value": "testing"}, {"@value": "more testing"}],
                "http://schema.org/license": [
                    {"@id": "https://spdx.org/licenses/Adobe-2006"},
                    {"@id": "https://spdx.org/licenses/Abstyles"},
                    {"@id": "https://spdx.org/licenses/AGPL-1.0-only"}
                ],
                "http://schema.org/name": [{"@value": "Test"}],
                "http://schema.org/operatingSystem": [{"@value": "Windows"}],
                "http://schema.org/programmingLanguage": [{"@value": "Python"}, {"@value": "Python 3"}],
                "http://schema.org/relatedLink": [{"@id": "https://docs.software-metadata.pub/en/latest"}],
                "http://schema.org/releaseNotes": [{"@value": "get it now"}],
                "http://schema.org/version": [{"@value": "1.1.1"}],
                "https://codemeta.github.io/terms/developmentStatus": [{"@id": "abandoned"}],
                "https://codemeta.github.io/terms/funding": [{"@value": "none :("}],
                "https://codemeta.github.io/terms/isSourceCodeOf": [{"@id": "HERMES"}],
                "https://codemeta.github.io/terms/issueTracker": [
                    {"@id": "https://github.com/softwarepub/hermes/issues"}
                ],
                "https://codemeta.github.io/terms/referencePublication": [{"@id": "https://arxiv.org/abs/2201.09015"}]
            })
        )
    ]
)
def test_codemeta_harvest(tmp_path, monkeypatch, codemeta, res):
    monkeypatch.chdir(tmp_path)

    codemeta_file = tmp_path / "codemeta.json"
    codemeta_file.write_text(codemeta)

    config_file = tmp_path / "hermes.toml"
    config_file.write_text("[harvest]\nsources = [ \"codemeta\" ]")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "harvest", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(context_manager.HermesContext.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit:
        manager = context_manager.HermesContext()
        manager.prepare_step("harvest")
        with manager["codemeta"] as cache:
            result = SoftwareMetadata(cache["codemeta"])
        manager.finalize_step("harvest")
    finally:
        sys.argv = orig_argv

    assert result.data_dict == res.data_dict
