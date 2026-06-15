# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import sys

import pytest

from hermes.commands import cli
from hermes.model import hermes_cache, SoftwareMetadata


@pytest.mark.parametrize(
    "process_result, res",
    [
        2 * (
            SoftwareMetadata({
                "@type": ["http://schema.org/SoftwareSourceCode"],
                "http://schema.org/description": [{"@value": "for testing"}],
                "http://schema.org/name": [{"@value": "Test"}]
            }),
        ),
        2 * (
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
            }),
        ),
    ]
)
def test_do_nothing_curate(tmp_path, monkeypatch, process_result, res):
    monkeypatch.chdir(tmp_path)

    manager = hermes_cache.HermesCacheManager(tmp_path)
    manager.prepare_step("process")
    with manager["result"] as cache:
        cache["expanded"] = process_result.ld_value
        cache["context"] = {"@context": process_result.full_context}
    manager.finalize_step("process")

    config_file = tmp_path / "hermes.toml"
    config_file.write_text("[curate]\nplugin = \"pass_curate\"")

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "curate", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(hermes_cache.HermesCacheManager.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager.prepare_step("curate")
        result = SoftwareMetadata.load_from_cache(manager, "result")
        manager.finalize_step("curate")
        sys.argv = orig_argv

    assert result.data_dict == res.data_dict
