# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

"""Basic CLI to list plugins from the Hermes market place."""

from html.parser import HTMLParser
from typing import List, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from hermes.utils import hermes_doi, hermes_user_agent

MARKETPLACE_URL = "https://hermes.software-metadata.pub"


class SchemaOrgModel(BaseModel):
    """Basic model for Schema.org JSON-LD validation and serialization."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    context_: str = Field(alias="@context", default="https://schema.org")
    type_: str = Field(alias="@type")
    id_: Optional[str] = Field(alias="@id", default=None)


class SchemaOrgOrganization(SchemaOrgModel):
    """Validation and serialization of ``schema:Organization``.

    This model does not incorporate all possible fields and is meant to be used merely
    for the purposes of the Hermes marketplace.
    """

    type_: str = Field(alias="@type", default="Organization")

    name: str


class SchemaOrgSoftwarePublication(SchemaOrgModel):
    """Validation and serialization of ``schema:SoftwarePublication``.

    This model does not incorporate all possible fields and is meant to be used merely
    for the purposes of the Hermes marketplace.
    """

    type_: str = Field(alias="@type", default="SoftwareApplication")

    name: str
    url: Optional[str] = None
    install_url: Optional[str] = None
    abstract: Optional[str] = None
    author: Optional[SchemaOrgOrganization] = None
    is_part_of: Optional["SchemaOrgSoftwarePublication"] = None
    keywords: List["str"] = None


schema_org_hermes = SchemaOrgSoftwarePublication(id_=hermes_doi, name="hermes")


class PluginMarketPlaceParser(HTMLParser):
    """Parser for the JSON-LD Schema.org markup used in the marketplace."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_json_ld: bool = False
        self.plugins: List[SchemaOrgSoftwarePublication] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and ("type", "application/ld+json") in attrs:
            self.is_json_ld = True

    def handle_endtag(self, tag):
        self.is_json_ld = False

    def handle_data(self, data):
        if self.is_json_ld:
            plugin = SchemaOrgSoftwarePublication.model_validate_json(data)
            self.plugins.append(plugin)


def main():
    response = requests.get(MARKETPLACE_URL, headers={"User-Agent": hermes_user_agent})
    response.raise_for_status()

    parser = PluginMarketPlaceParser()
    parser.feed(response.text)

    print(f"See the detailed list of plugins here: {MARKETPLACE_URL}#plugins")

    if parser.plugins:
        print()
        alignment = max(map(lambda plugin: len(plugin.name), parser.plugins)) + 1
        for plugin in parser.plugins:
            where = (
                "builtin"
                if plugin.is_part_of == schema_org_hermes
                else (plugin.url or "")
            )
            print(f"{plugin.name:>{alignment}} {where}")
        print()


if __name__ == "__main__":
    main()
