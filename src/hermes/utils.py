# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from importlib.metadata import metadata


hermes_metadata = metadata("hermes").json

hermes_name = hermes_metadata["name"]
hermes_version = hermes_metadata["version"]
hermes_homepage = hermes_metadata["home_page"]

hermes_user_agent = f"{hermes_name}/{hermes_version} ({hermes_homepage})"
