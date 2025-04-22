# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

import requests_mock

from hermes.commands.marketplace import (
    schema_org_hermes,
    SchemaOrgModel,
    _is_hermes_reference,
)


def test_schema_org_hermes_doi_is_absolute():
    """The HERMES DOI rendered to the plugins list must always be a full URL."""
    assert isinstance(schema_org_hermes, SchemaOrgModel)
    assert schema_org_hermes.id_ is not None
    assert schema_org_hermes.id_.startswith("https://doi.org/")


def test_concept_doi_is_hermes_reference():
    """The HERMES concept DOI is a reference to HERMES.

    We must be able to figure this out without asking DataCite.
    """
    with requests_mock.Mocker() as m:
        assert _is_hermes_reference(
            SchemaOrgModel(
                type_="SoftwareSourceCode",
                id_="https://doi.org/10.5281/zenodo.13221383",
            )
        )
        # DataCite API was not called
        assert m.call_count == 0


def test_is_hermes_reference_if_datacite_api_returns_concept_doi_as_rel_id():
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.datacite.org/dois/10.9999/fake.1000",
            text="""
{
  "data": {
    "id": "10.9999/fake.1000",
    "type": "dois",
    "attributes": {
      "doi": "10.9999/fake.1000",
      "prefix": "10.9999",
      "suffix": "fake.1000",
      "relatedIdentifiers": [
        {
          "relationType": "IsVersionOf",
          "relatedIdentifier": "10.5281/zenodo.13221383",
          "relatedIdentifierType": "DOI"
        }
      ]
    }
  }
}
""".strip(),
        )
        # 10.5281/zenodo.13221383 retured from DataCite is HERMES concept DOI
        assert _is_hermes_reference(
            SchemaOrgModel(
                type_="SoftwareSourceCode", id_="https://doi.org/10.9999/fake.1000"
            )
        )
        # DataCite API was called once
        assert m.call_count == 1


def test_not_is_hermes_reference_if_datacite_api_returns_wrong_rel_id():
    with requests_mock.Mocker() as m:
        m.get(
            "https://api.datacite.org/dois/10.9999/fake.2000",
            text="""
{
  "data": {
    "id": "10.9999/fake.2000",
    "type": "dois",
    "attributes": {
      "doi": "10.9999/fake.2000",
      "prefix": "10.9999",
      "suffix": "fake.2000",
      "relatedIdentifiers": [
        {
          "relationType": "IsVersionOf",
          "relatedIdentifier": "10.9999/fake.1999",
          "relatedIdentifierType": "DOI"
        }
      ]
    }
  }
}
""".strip(),
        )
        # 10.9999/fake.1999 returned from DataCite is not HERMES concept DOI
        assert not _is_hermes_reference(
            SchemaOrgModel(
                type_="SoftwareSourceCode", id_="https://doi.org/10.9999/fake.2000"
            )
        )
        # DataCite API was called once
        assert m.call_count == 1
