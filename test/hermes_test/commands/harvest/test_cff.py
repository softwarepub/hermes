# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import pathlib
import json
from ruamel.yaml import YAML

import pytest

import hermes.commands.harvest.cff as harvest


@pytest.fixture
def codemeta():
    return json.loads("""{
      "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
      "@type": "SoftwareSourceCode",
      "author": [
        {
          "@type": "Person",
          "name": "Author"
        }
      ],
      "name": "Title"
    }""")


@pytest.fixture
def valid_minimal_cff(tmp_path):
    cff = """\
    cff-version: 1.2.0
    authors:
      - name: Author
    message: Message
    title: Title
    """
    yaml = YAML()
    cff_yml = yaml.load(cff)
    cff_file = tmp_path / 'CITATION.cff'
    yaml.dump(cff_yml, cff_file)
    return cff_file


def test_convert_cff_to_codemeta(valid_minimal_cff, codemeta):
    actual_result = harvest._convert_cff_to_codemeta(valid_minimal_cff.read_text())
    assert codemeta == actual_result


def test_get_single_cff(tmp_path):
    assert harvest._get_single_cff(tmp_path) is None
    single_cff = tmp_path / 'CITATION.cff'
    single_cff.touch()
    assert harvest._get_single_cff(tmp_path) == single_cff


def test_validate_success(valid_minimal_cff):
    cff_dict = harvest._load_cff_from_file(valid_minimal_cff.read_text())
    assert harvest._validate(pathlib.Path("foobar"), cff_dict)


def test_validate_fail():
    assert harvest._validate(pathlib.Path("foobar"), {}) is False


# Regression test for https://github.com/hermes-hmc/workflow/issues/112

@pytest.fixture
def codemeta_with_email():
    return json.loads("""{
      "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
      "@type": "SoftwareSourceCode",
      "author": [
        {
          "@type": "Person",
          "email": "em@il.notexist",
          "name": "Author"
        }
      ],
      "name": "Title"
    }""")


@pytest.fixture
def valid_minimal_cff_with_email(tmp_path):
    cff = """\
    cff-version: 1.2.0
    authors:
      - name: Author
        email: em@il.notexist
    message: Message
    title: Title
    """
    yaml = YAML()
    cff_yml = yaml.load(cff)
    cff_file = tmp_path / 'CITATION.cff'
    yaml.dump(cff_yml, cff_file)
    return cff_file


def test_convert_cff_to_codemeta_with_email(valid_minimal_cff_with_email, codemeta_with_email):
    actual_result = harvest._convert_cff_to_codemeta(valid_minimal_cff_with_email.read_text())
    assert codemeta_with_email == actual_result
