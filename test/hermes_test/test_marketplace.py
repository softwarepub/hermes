# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

from hermes.commands.marketplace import schema_org_hermes, SchemaOrgModel


def test_schema_org_hermes_doi_is_absolute():
    """The HERMES DOI rendered to the plugins list must always be a full URL."""
    assert isinstance(schema_org_hermes, SchemaOrgModel)
    assert schema_org_hermes.id_ is not None
    assert schema_org_hermes.id_.startswith("https://doi.org/")
