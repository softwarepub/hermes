# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import sys

import pytest

from hermes.commands import cli
from hermes.model import context_manager, SoftwareMetadata


@pytest.mark.parametrize(
    "metadata_in, metadata_out",
    [
        (
            {
                "cff": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/description": [{"@value": "for testing"}],
                        "http://schema.org/name": [{"@value": "Test"}],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Test"}],
                                "http://schema.org/givenName": [{"@value": "Testi"}],
                            }
                        ],
                        "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                    }
                )
            },
            SoftwareMetadata(
                {
                    "@type": ["http://schema.org/SoftwareSourceCode"],
                    "http://schema.org/description": [{"@value": "for testing"}],
                    "http://schema.org/name": [{"@value": "Test"}],
                    "http://schema.org/author": [
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Test"}],
                            "http://schema.org/givenName": [{"@value": "Testi"}],
                        }
                    ],
                    "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                }
            ),
        ),
        (
            {
                "cff": SoftwareMetadata(
                    {
                        "type": "SoftwareSourceCode",
                        "author": [
                            {
                                "id": "https://orcid.org/0000-0003-4925-7248",
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "name": "German Aerospace Center (DLR)"
                                },
                                "email": "stephan.druskat@dlr.de"
                            },
                            {
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "name": "Forschungszentrum J\u00c3\u00bclich"
                                },
                                "email": "o.bertuch@fz-juelich.de",
                                "givenName": "Oliver"
                            },
                            {
                                "id": "https://orcid.org/0000-0001-8174-7795",
                                "type": "Person",
                                "email": "o.knodel@hzdr.de",
                                "familyName": "Knodel",
                                "givenName": "Oliver"
                            }
                        ],
                        "description": "Tool to automate software publication. Not stable yet.",
                        "identifier": "https://doi.org/10.5281/zenodo.13221384",
                        "license": "https://spdx.org/licenses/Apache-2.0"
                    }
                ),
                "codemeta": SoftwareMetadata(
                    {
                        "type": "SoftwareSourceCode",
                        "author": [
                            {
                                "id": "https://orcid.org/0000-0001-6372-3853",
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "legalName": "German Aerospace Center (DLR)"
                                },
                                "email": "michael.meinel@dlr.de",
                                "familyName": "Meinel",
                                "givenName": "Michael"
                            },
                            {
                                "id": "https://orcid.org/0000-0003-4925-7248",
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "legalName": "German Aerospace Center (DLR)"
                                },
                                "email": "stephan.druskat@dlr.de",
                                "familyName": "Druskat",
                                "givenName": "Stephan"
                            },
                            {
                                "id": "https://orcid.org/0000-0002-2702-3419",
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "legalName": "Forschungszentrum J\u00c3\u00bclich"
                                },
                                "email": "o.bertuch@fz-juelich.de",
                                "familyName": "Bertuch"
                            },
                            {
                                "id": "https://orcid.org/0000-0001-8174-7795",
                                "type": "Person",
                                "affiliation": {
                                    "type": "Organization",
                                    "legalName": "Helmholtz-Zentrum Dresden-Rossendorf (HZDR)"
                                },
                                "familyName": "Knodel",
                                "givenName": "Oliver"
                            }
                        ],
                        "identifier": "https://doi.org/10.5281/zenodo.13221384",
                        "license": "https://spdx.org/licenses/Apache-2.0",
                        "legalName": "hermes",
                        "version": "0.9.0"
                    },
                    extra_vocabs = {"legalName": {"@id": "http://schema.org/name"}}
                )
            },
            SoftwareMetadata(
                {
                    "type": "SoftwareSourceCode",
                    "schema:author": [
                        {
                            "id": "https://orcid.org/0000-0001-6372-3853",
                            "type": "Person",
                            "affiliation": {
                                "type": "Organization",
                                "legalName": "German Aerospace Center (DLR)"
                            },
                            "email": "michael.meinel@dlr.de",
                            "familyName": "Meinel",
                            "givenName": "Michael"
                        },
                        {
                            "id": "https://orcid.org/0000-0003-4925-7248",
                            "type": "Person",
                            "affiliation": {
                                "type": "Organization",
                                "legalName": "German Aerospace Center (DLR)"
                            },
                            "email": "stephan.druskat@dlr.de",
                            "familyName": "Druskat",
                            "givenName": "Stephan"
                        },
                        {
                            "id": "https://orcid.org/0000-0002-2702-3419",
                            "type": "Person",
                            "affiliation": {
                                "type": "Organization",
                                "legalName": "Forschungszentrum J\u00c3\u00bclich"
                            },
                            "email": "o.bertuch@fz-juelich.de",
                            "familyName": "Bertuch",
                            "givenName": "Oliver"
                        },
                        {
                            "id": "https://orcid.org/0000-0001-8174-7795",
                            "type": "Person",
                            "affiliation": {
                                "type": "Organization",
                                "legalName": "Helmholtz-Zentrum Dresden-Rossendorf (HZDR)"
                            },
                            "email": "o.knodel@hzdr.de",
                            "familyName": "Knodel",
                            "givenName": "Oliver"
                        }
                    ],
                    "description": "Tool to automate software publication. Not stable yet.",
                    "identifier": "https://doi.org/10.5281/zenodo.13221384",
                    "license": "https://spdx.org/licenses/Apache-2.0",
                    "legalName": "hermes",
                    "version": "0.9.0"
                },
                extra_vocabs = {"legalName": {"@id": "http://schema.org/name"}}
            ),
        )
    ],
)
def test_process(tmp_path, monkeypatch, metadata_in, metadata_out):
    monkeypatch.chdir(tmp_path)

    manager = context_manager.HermesContext(tmp_path)
    manager.prepare_step("harvest")
    for harvester, result in metadata_in.items():
        with manager[harvester] as cache:
            cache["codemeta"] = result.compact()
            cache["context"] = {"@context": result.full_context}
            cache["expanded"] = result.ld_value
    manager.finalize_step("harvest")

    config_file = tmp_path / "hermes.toml"
    config_file.write_text(
        '[process]\nplugins=["codemeta"]\n'
        "[harvest]\nsources = [" + ", ".join('"' + f"{harvester}" + '"' for harvester in metadata_in) + "]"
    )

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "process", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(context_manager.HermesContext.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager.prepare_step("process")
        result = SoftwareMetadata.load_from_cache(manager, "result")
        manager.finalize_step("process")
        sys.argv = orig_argv

    assert result == metadata_out


@pytest.mark.parametrize(
    "metadata_in, metadata_out",
    [
        (
            {
                "cff": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/name": [{"@value": "Test"}],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Test"}],
                                "http://schema.org/email": [{"@value": "test.testi@testis.tests"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testers"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Tester"}],
                                "http://schema.org/email": [{"@value": "test@tester.tests"}],
                            },
                        ],
                        "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                    }
                ),
                "codemeta": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/description": [{"@value": "for testing"}],
                        "http://schema.org/name": [{"@value": "Test"}, {"@value": "Testis Test"}],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Test"}],
                                "http://schema.org/givenName": [{"@value": "Testi"}],
                                "http://schema.org/email": [
                                    {"@value": "test.testi@testis.tests"},
                                    {"@value": "test.testi@testis.tests2"},
                                ],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testers"}],
                            },
                        ],
                    }
                ),
            },
            SoftwareMetadata(
                {
                    "@type": ["http://schema.org/SoftwareSourceCode"],
                    "http://schema.org/description": [{"@value": "for testing"}],
                    "http://schema.org/name": [{"@value": "Test"}, {"@value": "Testis Test"}],
                    "http://schema.org/author": [
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Test"}],
                            "http://schema.org/givenName": [{"@value": "Testi"}],
                            "http://schema.org/email": [
                                {"@value": "test.testi@testis.tests"},
                                {"@value": "test.testi@testis.tests2"},
                            ],
                        },
                        {"@type": "http://schema.org/Person", "http://schema.org/familyName": [{"@value": "Testers"}]},
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Tester"}],
                            "http://schema.org/email": [{"@value": "test@tester.tests"}],
                        },
                    ],
                    "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                }
            ),
        ),
        (
            {
                "python": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testers"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Tester"}],
                                "http://schema.org/email": [{"@value": "test@tester.tests"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testis"}],
                                "http://schema.org/email": [{"@value": "testis.testis@tester.tests"}],
                            },
                        ],
                    }
                ),
                "cff": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/name": [{"@value": "Test"}],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Test"}],
                                "http://schema.org/email": [{"@value": "test.testi@testis.tests"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testers"}],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Tester"}],
                                "http://schema.org/email": [{"@value": "test@tester.tests"}],
                            },
                        ],
                        "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                    }
                ),
                "codemeta": SoftwareMetadata(
                    {
                        "@type": ["http://schema.org/SoftwareSourceCode"],
                        "http://schema.org/description": [{"@value": "for testing"}],
                        "http://schema.org/name": [{"@value": "Test"}, {"@value": "Testis Test"}],
                        "http://schema.org/author": [
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Test"}],
                                "http://schema.org/givenName": [{"@value": "Testi"}],
                                "http://schema.org/email": [
                                    {"@value": "test.testi@testis.tests"},
                                    {"@value": "test.testi@testis.tests2"},
                                ],
                            },
                            {
                                "@type": "http://schema.org/Person",
                                "http://schema.org/familyName": [{"@value": "Testers"}],
                            },
                        ],
                    }
                ),
            },
            SoftwareMetadata(
                {
                    "@type": ["http://schema.org/SoftwareSourceCode"],
                    "http://schema.org/description": [{"@value": "for testing"}],
                    "http://schema.org/name": [{"@value": "Test"}, {"@value": "Testis Test"}],
                    "http://schema.org/author": [
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Test"}],
                            "http://schema.org/givenName": [{"@value": "Testi"}],
                            "http://schema.org/email": [
                                {"@value": "test.testi@testis.tests"},
                                {"@value": "test.testi@testis.tests2"},
                            ],
                        },
                        {"@type": "http://schema.org/Person", "http://schema.org/familyName": [{"@value": "Testers"}]},
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Tester"}],
                            "http://schema.org/email": [{"@value": "test@tester.tests"}],
                        },
                        {
                            "@type": "http://schema.org/Person",
                            "http://schema.org/familyName": [{"@value": "Testis"}],
                            "http://schema.org/email": [{"@value": "testis.testis@tester.tests"}],
                        },
                    ],
                    "http://schema.org/license": [{"@id": "https://spdx.org/licenses/Apache-2.0"}],
                }
            ),
        ),
    ],
)
def test_process_complex(tmp_path, monkeypatch, metadata_in, metadata_out):
    monkeypatch.chdir(tmp_path)

    manager = context_manager.HermesContext(tmp_path)
    manager.prepare_step("harvest")
    for harvester, result in metadata_in.items():
        with manager[harvester] as cache:
            cache["codemeta"] = result.compact()
            cache["context"] = {"@context": result.full_context}
            cache["expanded"] = result.ld_value
    manager.finalize_step("harvest")

    config_file = tmp_path / "hermes.toml"
    config_file.write_text(
        '[process]\nplugins=["codemeta"]\n'
        "[harvest]\nsources = [" + ", ".join('"' + f"{harvester}" + '"' for harvester in metadata_in) + "]"
    )

    orig_argv = sys.argv[:]
    sys.argv = ["hermes", "process", "--path", str(tmp_path), "--config", str(config_file)]
    result = {}
    try:
        monkeypatch.setattr(context_manager.HermesContext.__init__, "__defaults__", (tmp_path.cwd(),))
        cli.main()
    except SystemExit as e:
        if e.code != 0:
            raise e
    finally:
        manager.prepare_step("process")
        result = SoftwareMetadata.load_from_cache(manager, "result")
        manager.finalize_step("process")
        sys.argv = orig_argv

    assert result == metadata_out
