import pytest

from hermes.commands.harvest.cff import CffHarvestPlugin


@pytest.fixture
def plugin():
    return CffHarvestPlugin()


@pytest.fixture
def valid_cff(plugin):
    cff_str = """
    cff-version: 1.2.0
    message: "If you use this software, please cite it as below."
    authors:
      - family-names: Druskat
        given-names: Stephan
        orcid: https://orcid.org/1234-5678-9101-1121
        email: stephan.druskat@dlr.de
      - name: German Aerospace Center
    title: "My Research Software"
    version: 2.0.4
    identifiers:
      - type: doi
        value: 10.5281/zenodo.1234
    date-released: 2021-08-11
    """
    cff = plugin._load_cff_from_file(cff_str)
    return cff


def test_load_cff_from_file(plugin):
    assert plugin._load_cff_from_file('invalid: "file"') == {"invalid": "file"}
    assert plugin._load_cff_from_file('timestamp: 10:01') == {"timestamp": "10:01"}
    assert plugin._load_cff_from_file('timestamp-str: "10:01"') == {"timestamp-str": "10:01"}

def test_patch_author_emails(plugin, valid_cff):
    codemeta = plugin._patch_author_emails(valid_cff, {"author": [{}]})
    assert codemeta == {"author": [{"email": "stephan.druskat@dlr.de"}]}
    codemeta2 = plugin._patch_author_emails(valid_cff, codemeta)
    assert codemeta2 == {"author": [{"email": "stephan.druskat@dlr.de"}]}
    codemeta3 = plugin._patch_author_emails(valid_cff, {"author": [{"email": "a@b.cd"}]})
    assert codemeta3 == {"author": [{"email": "stephan.druskat@dlr.de"}]}
