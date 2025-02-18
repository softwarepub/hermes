# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from importlib.metadata import metadata


hermes_metadata = metadata("hermes")

hermes_name = hermes_metadata["name"]
hermes_version = hermes_metadata["version"]
hermes_homepage = hermes_metadata["home-page"]

# TODO: Fetch this from somewhere
hermes_doi = "10.5281/zenodo.13311079"  # hermes v0.8.1

hermes_user_agent = f"{hermes_name}/{hermes_version} ({hermes_homepage})"
