from hermes.model.ld_utils import jsonld_dict


def test_jsonld_dict_value():
    data = jsonld_dict(**{
        "@context": ["https://schema.org"],
        "https://schema.org/name": [{"@value": "HERMES Test"}],
    })

    assert data["https://schema.org/name", "value"] == "HERMES Test"


def test_jsonld_dict_list():
    data = jsonld_dict(**{
        "@context": ["https://schema.org"],
        "https://schema.org/license": [{"@list": [
            {"https://schema.org/url": [{"@value": "https://spdx.com/Apache-2"}]},
            {"https://schema.org/url": [{"@value": "https://spdx.com/LGPL-3.0"}]},
        ]}],
    })

    licenses = data["https://schema.org/license", "value"]
    assert len(licenses) == 2
    assert licenses[0]["https://schema.org/url", "value"] == "https://spdx.com/Apache-2"
    assert licenses[1]["https://schema.org/url", "value"] == "https://spdx.com/LGPL-3.0"
