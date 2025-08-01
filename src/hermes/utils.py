# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from importlib.metadata import metadata


def retrieve_project_urls(metadata_urls: list[str]) -> dict[str, str]:
    """
    Extracts the keys and values from the project.urls section in distribution package metadata
    and converts them into a dictionary.

    :param metadata_urls: The list of urls to extract from (from distribution metadata)
    :return: A dictionary mapping URL names to URLs
    """
    return {
        url_lst[0].lower(): url_lst[1]
        for url_lst in [
            metadata_url_item.split(", ", maxsplit=1)
            for metadata_url_item in metadata_urls
        ]
    }


hermes_metadata = metadata("hermes")

# Basic metadata
hermes_name = hermes_metadata["name"]
hermes_version = hermes_metadata["version"]

# Project URLs
hermes_urls = retrieve_project_urls(hermes_metadata.get_all("project-url", []))
hermes_homepage = hermes_urls["homepage"]

# Publication metadata
# TODO: Fetch this from somewhere
hermes_doi = "10.5281/zenodo.13311079"  # hermes v0.8.1
hermes_concept_doi = "10.5281/zenodo.13221383"
"""Fix "concept" DOI that always refers to the newest version."""

# User agent
hermes_user_agent = f"{hermes_name}/{hermes_version} ({hermes_homepage})"
