# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR), German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>

from importlib.metadata import metadata
from mimetypes import guess_type
from pathlib import Path
import argparse


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


def guess_file_type(path: Path):
    """File type detection for non-standardised formats.

    Custom detection for file types not yet supported by Python's ``guess_type``
    function.
    """
    # YAML was only added to ``guess_type`` in Python 3.14 due to the MIME type only
    # having been decided in 2024.
    # See: https://www.rfc-editor.org/rfc/rfc9512.html
    if path.suffix in [".yml", ".yaml"]:
        return ("application/yaml", None)

    # TOML is not yet part of ``guess_type`` due to the MIME type only having been
    # accepted in October of 2024.
    # See: https://www.iana.org/assignments/media-types/application/toml
    if path.suffix == ".toml":
        return ("application/toml", None)

    # cff is yaml.
    # See: https://github.com/citation-file-format/citation-file-format/issues/391
    if path.name == "CITATION.cff":
        return ("application/yaml", None)

    # .license files are likely license annotations according to REUSE specification.
    # See: https://reuse.software/spec/
    if path.suffix == ".license":
        return ("text/plain", None)

    if path.name == "poetry.lock":
        return ("text/plain", None)

    # use non-strict mode to cover more file types
    return guess_type(path, strict=False)

def mask_options_values(args: argparse.Namespace) -> argparse.Namespace:
    """Masks potentially sensitive values in the 'options' argument
    in the passed argparse.Namespace.

    The main use case for this is preventing potentially sensitive
    data/secrets being included in raw args logging.

    :param args: The argparse.Namespace to mask.
    :return: A copy of the namespace with masked sensitive values.
    """
    import copy

    masked_args = copy.copy(args)

    # Mask the values for 'options' if they exist
    if hasattr(masked_args, "options") and masked_args.options:
        masked_args.options = [
            (key, "***REDACTED***") for key, value in masked_args.options
        ]

    return masked_args
