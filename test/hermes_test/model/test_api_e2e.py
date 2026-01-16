# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import pytest
from hermes.commands.harvest.cff import CffHarvestPlugin, CffHarvestSettings
from hermes.commands.harvest.codemeta import CodeMetaHarvestPlugin
from hermes.model import SoftwareMetadata


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
def test_cff_harvest(tmp_path, cff, res):
    class Args:
        def __init__(self, path):
            self.path = path

    class Settings:
        def __init__(self, cff_settings):
            self.cff = cff_settings

    class Command:
        def __init__(self, args, settings):
            self.args = args
            self.settings = settings

    command = Command(Args(tmp_path), Settings(CffHarvestSettings()))

    cff_file = tmp_path / "CITATION.cff"
    cff_file.write_text(cff)

    result = CffHarvestPlugin().__call__(command)
    # FIXME: update to compare the SoftwareMetadata objects instead of the data_dicts (in multiple places)
    # after merge with refactor/data-model and/or refactor/423-implement-public-api
    assert result[0].data_dict == res.data_dict


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
        )
    ]
)
def test_codemeta_harvest(tmp_path, codemeta, res):
    class Args:
        def __init__(self, path):
            self.path = path

    class Command:
        def __init__(self, args):
            self.args = args

    command = Command(Args(tmp_path))

    codemeta_file = tmp_path / "codemeta.json"
    codemeta_file.write_text(codemeta)

    result = CodeMetaHarvestPlugin().__call__(command)
    assert result[0].data_dict == res.data_dict
