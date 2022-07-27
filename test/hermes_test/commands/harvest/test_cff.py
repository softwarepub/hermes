from collections import deque
import json
from ruamel.yaml import YAML

import pytest

import hermes.commands.harvest as harvest


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


@pytest.fixture()
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
    actual_result = harvest.convert_cff_to_codemeta(valid_minimal_cff)
    assert codemeta == actual_result


@pytest.mark.parametrize("path, path_str", [
    (deque(['str1', 0]), "'str1 1'"),
    (deque(['str1', 0, 'str2', 1, 'str3', 2]), "'str1 1 -> str2 2 -> str3 3'"),
])
def test_build_path_str(path, path_str):
    assert harvest.build_path_str(path) == path_str


@pytest.mark.parametrize("path, path_str", [
    ('str1', "'str1 1'"),
    (deque([0, 'str1', 1, 'str2', 2, 'str3']), "'str1 1 -> str2 2 -> str3 3'"),
])
def test_build_path_str_fail(path, path_str):
    with pytest.raises(Exception):
        assert harvest.build_path_str(path) == path_str


def test_get_single_cff(tmp_path):
    assert harvest.get_single_cff(tmp_path) is None
    single_cff = tmp_path / 'CITATION.cff'
    single_cff.touch()
    assert harvest.get_single_cff(tmp_path) == str(single_cff)


def test_validate():
    assert False
