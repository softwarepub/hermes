# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf, German Aerospace Center (DLR)
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Stephan Druskat

"""Basic CLI to list plugins from the Hermes marketplace."""
from html.parser import HTMLParser
from typing import List, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from hermes.utils import hermes_doi, hermes_user_agent

MARKETPLACE_URL = "https://hermes.software-metadata.pub/marketplace"


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

    def model_dump_jsonld(self):
        return self.model_dump_json(by_alias=True, exclude_none=True)


class SchemaOrgOrganization(SchemaOrgModel):
    """Validation and serialization of ``schema:Organization``.

    This model does not incorporate all possible fields and is meant to be used merely
    for the purposes of the Hermes marketplace.
    """

    type_: str = Field(alias="@type", default="Organization")

    name: str


class SchemaOrgSoftwareApplication(SchemaOrgModel):
    """Validation and serialization of ``schema:SoftwareApplication``.

    This model does not incorporate all possible fields and is meant to be used merely
    for the purposes of the Hermes marketplace.
    """

    type_: str = Field(alias="@type", default="SoftwareApplication")

    name: str
    url: Optional[str] = None
    install_url: Optional[str] = None
    abstract: Optional[str] = None
    author: Optional[SchemaOrgOrganization] = None
    is_part_of: Optional["SchemaOrgSoftwareApplication"] = None
    keywords: List["str"] = None


schema_org_hermes = SchemaOrgSoftwareApplication(id_=hermes_doi, name="hermes")


class PluginMarketPlaceParser(HTMLParser):
    """Parser for the JSON-LD Schema.org markup used in the marketplace."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_json_ld: bool = False
        self.plugins: List[SchemaOrgSoftwareApplication] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and ("type", "application/ld+json") in attrs:
            self.is_json_ld = True

    def handle_endtag(self, tag):
        self.is_json_ld = False

    def handle_data(self, data):
        if self.is_json_ld:
            plugin = SchemaOrgSoftwareApplication.model_validate_json(data)
            self.plugins.append(plugin)


def _sort_plugins_by_step(plugins: list[SchemaOrgSoftwareApplication]) -> dict[str, list[SchemaOrgSoftwareApplication]]:
    sorted_plugins = {k: [] for k in ["harvest", "process", "curate", "deposit", "postprocess"]}
    for p in plugins:
        for kw in p.keywords:
            if kw.startswith("hermes-step-"):
                sorted_plugins[kw.removeprefix("hermes-step-")].append(p)
    return sorted_plugins


def main():
    response = requests.get(MARKETPLACE_URL, headers={"User-Agent": hermes_user_agent})
    response.raise_for_status()

    parser = PluginMarketPlaceParser()
    parser.feed(response.text)

    print(
        "A detailed list of available plugins can be found on the HERMES website at",
        MARKETPLACE_URL + "."
    )

    def _plugin_loc(_plugin: SchemaOrgSoftwareApplication) -> str:
        return "builtin" if _plugin.is_part_of == schema_org_hermes else (_plugin.url or "")

    if parser.plugins:
        print()
        max_name_len = max(map(lambda plugin: len(plugin.name), parser.plugins))
        max_loc_len = max(map(lambda plugin: len(_plugin_loc(plugin)), parser.plugins))
        row_sep = "-" * (17 + max_name_len + max_loc_len)
        print("HERMES step   " + "Plugin name" + (" " * (max_name_len - 8)) + "Plugin location")
        print(row_sep)
        plugins_sorted = _sort_plugins_by_step(parser.plugins)
        for step in plugins_sorted.keys():
            for plugin in plugins_sorted[step]:
                print(f"{step:>11}   {plugin.name:{max_name_len}}   {_plugin_loc(plugin)}")
        print(row_sep)
        print()


if __name__ == "__main__":
    main()
