import pytest
from hermes.commands.harvest.cff import CffHarvestPlugin, CffHarvestSettings
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
                "schema:author": {
                    "@list": [{
                        "@type": "Person",
                        "email": ["max@muster.mann"],
                        "familyName": ["Mustermann"],
                        "givenName": ["Max"]
                    }]
                },
                "schema:name": ["Temp"]
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
    # FIXME: update to compare the SoftwareMetadata objects instead of the data_dicts
    # after merge with refactor/data-model and/or refactor/423-implement-public-api
    assert result[0].data_dict == res.data_dict
