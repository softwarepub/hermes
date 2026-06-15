# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import sys

import pytest

from hermes.commands import cli
from hermes.model import hermes_cache, SoftwareMetadata


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
        monkeypatch.setattr(hermes_cache.HermesCacheManager.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager = hermes_cache.HermesCacheManager()
        manager.prepare_step("harvest")
        result = SoftwareMetadata.load_from_cache(manager, "codemeta")
        manager.finalize_step("harvest")
        sys.argv = orig_argv

    assert result == res
