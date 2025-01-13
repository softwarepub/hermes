import pytest

from hermes.commands.harvest.cff import CffHarvestPlugin


@pytest.fixture
def plugin():
    return CffHarvestPlugin()


def test_load_cff_from_file(plugin):
    assert plugin._load_cff_from_file('invalid: "file"') == {"invalid": "file"}
    assert plugin._load_cff_from_file('timestamp: 10:01') == {"timestamp": "10:01"}
    assert plugin._load_cff_from_file('timestamp-str: "10:01"') == {"timestamp-str": "10:01"}
