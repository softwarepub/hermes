# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat

import json

import pytest
from hermes.model.errors import HermesValidationError

import hermes.commands.harvest.codemeta as harvest


INVALID_CODEMETA_JSON = """\
{
  "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
  "@type": "SoftwareSourceCode",
  "INVALID_KEY": "HERMES"
}
"""

INVALID_JSON = 'Not JSON'

CODEMETA_JSON = """\
{
  "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
  "@type": "SoftwareSourceCode",
  "identifier": "HERMES",
  "description": "HERMES Workflow.",
  "name": "HERMES Workflow",
  "codeRepository": "https://github.com/hermes-hmc/workflow",
  "issueTracker": "https://github.com/hermes-hmc/workflow/issues",
  "license": "https://spdx.org/licenses/Apache-2.0",
  "version": "2.0",
  "author": [
    {
      "@type": "Person",
      "givenName": "Iam",
      "familyName": "Person",
      "email": "iam@email.com",
      "@id": "http://orcid.org/0000-0000-0000-0000"
    }
  ],
  "contributor": [
    {
      "@type": "Person",
      "givenName": "Iam",
      "familyName": "Person",
      "email": "iam@email.com",
      "@id": "http://orcid.org/0000-0000-0000-0000"
    }
  ],
  "maintainer":     {
    "@type": "Person",
    "givenName": "Iam",
    "familyName": "Person",
    "email": "iam@email.com",
    "@id": "http://orcid.org/0000-0000-0000-0000"
  },
  "contIntegration": "https://github.com/hermes-hmc/workflow/actions",
  "developmentStatus": "active",
  "downloadUrl": "https://github.com/hermes-hmc/workflow",
  "funder": {
          "@id": "https://helmholtz-metadaten.de",
          "@type": "Organization",
          "name": "Helmholtz Metadata Collaboration"
  },
  "funding":"ZT-I-PF-3-006; HERMES: Helmholtz Rich Metadata Software Publication",
  "keywords": [
    "metadata",
    "software publication",
    "automation"
  ],
  "dateCreated":"2020-07-01",
  "datePublished":"2022-11-23",
  "programmingLanguage": "Python"
}
"""


@pytest.fixture
def valid_codemeta():
    return json.loads(CODEMETA_JSON)


@pytest.fixture
def invalid_codemeta():
    return json.loads(INVALID_CODEMETA_JSON)


@pytest.fixture()
def valid_codemeta_path(tmp_path, valid_codemeta):
    codemeta_path = tmp_path / 'codemeta.json'
    with open(codemeta_path, 'w') as fo:
        json.dump(valid_codemeta, fo)
    return codemeta_path


@pytest.fixture()
def invalid_codemeta_path(tmp_path, invalid_codemeta):
    codemeta_path = tmp_path / 'codemeta.json'
    with open(codemeta_path, 'w') as fo:
        json.dump(invalid_codemeta, fo)
    return codemeta_path


@pytest.fixture()
def invalid_json_path(tmp_path):
    codemeta_path = tmp_path / 'codemeta.json'
    with open(codemeta_path, 'w') as fo:
        fo.write(INVALID_JSON)
    return codemeta_path


def test_get_single_codemeta(tmp_path):
    assert harvest._get_single_codemeta(tmp_path) is None
    single_codemeta = tmp_path / 'codemeta.json'
    single_codemeta.touch()
    assert harvest._get_single_codemeta(tmp_path) == single_codemeta


def test_validate_invalid_json_raises(invalid_json_path, tmp_path):
    with pytest.raises(HermesValidationError) as e:
        harvest._validate(invalid_json_path)
        assert "cannot be decoded into JSON" in e.value


def test_validate_invalid_codemeta(invalid_codemeta_path, tmp_path):
    with pytest.raises(HermesValidationError, match="Validation of CodeMeta file failed."):
        harvest._validate(invalid_codemeta_path)


def test_validate_success(valid_codemeta_path):
    assert harvest._validate(valid_codemeta_path)
