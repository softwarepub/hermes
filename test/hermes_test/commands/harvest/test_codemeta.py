import pathlib
import json

import pytest

import hermes.commands.harvest.codemeta as harvest


CODEMETA_JSON = """\
{
    "@context": [
        "https://raw.githubusercontent.com/codemeta/codemeta/2.0/codemeta.jsonld",
        "https://raw.githubusercontent.com/schemaorg/schemaorg/main/data/releases/13.0/schemaorgcontext.jsonld",
        "https://w3id.org/software-types",
        "https://w3id.org/software-iodata"
    ],
    "@id": "https://github.com/hermes-hms/workflow.git",
    "@type": "SoftwareSourceCode",
    "applicationCategory": "Software Development",
    "audience": {
        "@id": "/audience/developers",
        "@type": "Audience",
        "audienceType": "Developers"
    },
    "author": {
        "@id": "/person/iam-person",
        "@type": "Person",
        "affiliation": {
            "@id": "/org/iamorg",
            "@type": "Organization",
            "name": "iamorg"
        },
        "email": "iam@mail.example",
        "familyName": "Person",
        "givenName": "Iam",
        "position": 1,
        "url": "https://iam.website"
    },
    "codeRepository": "https://github.com/hermes-hms/workflow.git",
    "contributor": {
        "@id": "/person/iam-person",
        "@type": "Person",
        "affiliation": {
            "@id": "/org/iamorg",
            "@type": "Organization",
            "name": "iamorg"
        },
        "email": "iam@mail.example",
        "familyName": "Person",
        "givenName": "Iam",
        "position": 1,
        "url": "https://iam.website"
    },
    "dateCreated": "2023-06-31T10:54:22Z+0200",
    "dateModified": "2023-12-31T121:52:34Z+0200",
    "description": "Test Codemeta harvesting",
    "developmentStatus": "https://www.repostatus.org/#active",
    "identifier": "workflow",
    "issueTracker": "https://github.com/hermes-hmc/workflow/issues",
    "keywords": [
        "metadata",
        "scientific",
        "codemeta",
        "hermes",
        "software metadata",
        "software publication"
    ],
    "license": [
        "https://spdx.org/licenses/Apache-2.0"
    ],
    "maintainer": {
        "@id": "/person/iam-person",
        "@type": "Person",
        "affiliation": {
            "@id": "/org/iamorg",
            "@type": "Organization",
            "name": "iamorg"
        },
        "email": "iam@mail.example",
        "familyName": "Person",
        "givenName": "Iam",
        "position": 1,
        "url": "https://iam.website"
    },
    "name": "HERMES Workflow",
    "operatingSystem": [
        "Linux",
        "BSD",
        "macOS"
    ],
    "readme": "https://github.com/hermes-hmc/workflow/blob/main/README.md",
    "runtimePlatform": [
        "Python 3.10"
    ],
    "softwareRequirements": [
        {
            "@id": "/dependency/click",
            "@type": "SoftwareApplication",
            "identifier": "click",
            "name": "click",
            "runtimePlatform": "Python 3"
        }
    ],
    "targetProduct": {
        "@id": "/commandlineapplication/haggis",
        "@type": "CommandLineApplication",
        "executableName": "haggis",
        "name": "haggis",
        "runtimePlatform": "Python 3"
    },
    "url": [
        "https://software-metadata.pub",
        "https://github.com/hermes-hmc/workflow.git"
    ],
    "version": "0"
}
"""


@pytest.fixture
def codemeta():
    return json.loads(CODEMETA_JSON)


@pytest.fixture()
def valid_codemeta(tmp_path):
    codemeta_json = json.loads(CODEMETA_JSON)
    codemeta_file = tmp_path / 'codemeta.json'
    json.dump(codemeta_json, codemeta_file)
    return codemeta_file


def test_get_single_codemeta(tmp_path):
    assert harvest._get_single_codemeta(tmp_path) is None
    single_codemeta = tmp_path / 'codemeta.json'
    single_codemeta.touch()
    assert harvest._get_single_codemeta(tmp_path) == single_codemeta


def test_validate_success(codemeta):
    assert harvest._validate(pathlib.Path("foobar"))
