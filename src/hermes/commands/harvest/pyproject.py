# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pathlib
import toml

from pydantic import BaseModel

from hermes.commands.harvest.base import HermesHarvestPlugin
from hermes.model.types import ld_dict, ld_context


class PyprojectHarvestSettings(BaseModel):
    """Custom settings for CFF harvester."""
    source_path: pathlib.Path = "pyproject.toml"


class PyprojectHarvestPlugin(HermesHarvestPlugin):
    settings_class = PyprojectHarvestSettings

    def __call__(self, command):
        with self.prov_doc.make_node(
                "Activity", {"schema:name": "load file", "prov:wasStartedBy": self.plugin_node.ref}
        ) as load_activity:
            project_file = pathlib.Path(command.settings.pyproject.source_path)
            toml_data = toml.load(project_file)
            project_data = toml_data["project"]

            load_activity.add_related(
                "prov:used", "Entity",
                {"url": project_file.absolute().as_uri(), "schema:text": project_file.read_text()}
            )

        codemeta = ld_dict.from_dict({
            "@context": ld_context.HERMES_BASE_CONTEXT,
            "@type": "SoftwareSourceCode",

            "name": project_data["name"],
            "version": project_data["version"],
            "description": project_data["description"],
            "author": [
                {"@type": "Person", "name": author["name"], "email": author["email"]}
                for author in project_data["authors"]
            ],
            "runtimePlatform": f"Python {project_data['requires-python']}",
            "keyword": project_data["keywords"],
            "license": f"https://spdx.org/licenses/{project_data['license']}",
        })

        return codemeta
