# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf, German Aerospace Center (DLR)
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Stephan Druskat

"""Basic CLI to list plugins from the Hermes marketplace."""

from functools import cache
from html.parser import HTMLParser
from typing import List, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from hermes.commands.init.util import slim_click
from hermes.utils import hermes_doi, hermes_concept_doi, hermes_user_agent

MARKETPLACE_URL = "https://docs.software-metadata.pub/en/latest/plugins/marketplace.html"


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


schema_org_hermes = SchemaOrgSoftwareApplication(
    id_=(
        hermes_doi
        if hermes_doi.startswith("https://doi.org/")
        else f"https://doi.org/{hermes_doi}"
    ),
    name="hermes",
)


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

    def parse_plugins_from_url(self, url: str = MARKETPLACE_URL, user_agent: str = hermes_user_agent):
        response = requests.get(url, headers={"User-Agent": user_agent})
        response.raise_for_status()
        self.feed(response.text)


@cache
def _doi_is_version_of_concept_doi(doi: str, concept_doi: str) -> bool:
    """Check whether ``doi`` is a version of ``concept_doi``.

    The check is performed by requesting ``doi`` from the DataCite API and checking
    whether its related identifier of type ``IsVersionOf`` points to ``concept_doi``.
    This is the case if ``conecpt_doi`` is the concept DOI of ``doi``.
    """

    doi = doi.removeprefix("https://doi.org/")
    concept_doi = concept_doi.removeprefix("https://doi.org/")

    response = requests.get(
        f"https://api.datacite.org/dois/{doi}",
        headers={"User-Agent": hermes_user_agent},
    )
    response.raise_for_status()

    for identifier in response.json()["data"]["attributes"]["relatedIdentifiers"]:
        if (
            identifier["relationType"] == "IsVersionOf"
            and identifier["relatedIdentifier"] == concept_doi
        ):
            return True

    return False


def _is_hermes_reference(reference: Optional[SchemaOrgModel]):
    """Figure out whether ``reference`` refers to HERMES."""
    if reference is None:
        return False

    if reference.id_ in [
        schema_org_hermes.id_,
        hermes_concept_doi,
        f"https://doi.org/{hermes_concept_doi}",
    ]:
        return True

    return _doi_is_version_of_concept_doi(reference.id_, hermes_concept_doi)


def _sort_plugins_by_step(plugins: list[SchemaOrgSoftwareApplication]) -> dict[str, list[SchemaOrgSoftwareApplication]]:
    sorted_plugins = {k: [] for k in ["harvest", "process", "curate", "deposit", "postprocess"]}
    for p in plugins:
        for kw in p.keywords:
            if kw.startswith("hermes-step-"):
                sorted_plugins[kw.removeprefix("hermes-step-")].append(p)
    return sorted_plugins


def _plugin_loc(_plugin: SchemaOrgSoftwareApplication) -> str:
    return (
        "builtin"
        if _is_hermes_reference(_plugin.is_part_of)
        else (_plugin.url or "")
    )


def main():
    parser = PluginMarketPlaceParser()
    parser.parse_plugins_from_url(MARKETPLACE_URL, hermes_user_agent)

    print(
        "A detailed list of available plugins can be found on the HERMES website at",
        MARKETPLACE_URL + "."
    )

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


class PluginInfo:
    """
    This class contains all the information about a plugin which are needed for the init-Command.
    """
    def __init__(self):
        self.name: str = ""
        self.location: str = ""
        self.step: str = ""
        self.builtin: bool = True
        self.install_url: str = ""
        self.abstract: str = ""

    def __str__(self):
        step_text = f"[{self.step}]"
        return f"{step_text} {slim_click.Formats.BOLD.wrap_around(self.name)} ({self.location})"

    def get_pip_install_command(self) -> str:
        """
        Returns the pip install command which can be used to install the plugin.
        Tries to extract the project name from the install_url (PyPI-URL) if possible.
        Otherwise, it tries to use the location (Git-Project-URL) for the pip install command.
        """
        if self.install_url and self.install_url.startswith("https://pypi.org/project/"):
            project_name = self.install_url.rstrip("/").removeprefix("https://pypi.org/project/")
            return f"pip install {project_name}"
        if self.location and self.location.startswith(("https://", "git@", "ssh://")):
            git_url = self.location.rstrip("/")
            return f"pip install git+{git_url}"
        return ""

    def is_valid(self) -> bool:
        """
        Returns True if the plugin can be installed. Maybe we'll check the actual repository here later
        to make sure that other things are valid too.
        """
        return self.get_pip_install_command() != ""


def get_plugin_infos() -> list[PluginInfo]:
    """
    Returns a List of PluginInfos which are meant to be used by the init-command.
    """
    parser = PluginMarketPlaceParser()
    parser.parse_plugins_from_url(MARKETPLACE_URL, hermes_user_agent)
    infos: list[PluginInfo] = []
    if parser.plugins:
        plugins_sorted = _sort_plugins_by_step(parser.plugins)
        for step in plugins_sorted.keys():
            for plugin in plugins_sorted[step]:
                info = PluginInfo()
                info.name = plugin.name
                info.step = step
                info.location = _plugin_loc(plugin)
                info.builtin = info.location == "builtin"
                info.install_url = plugin.install_url
                info.abstract = plugin.abstract
                infos.append(info)
    return infos
