# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import typing as t

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context_manager import HermesContext
from hermes.model.errors import HermesValidationError


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> t.Tuple[t.Dict, t.Dict]:
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args

        # Initialize the harvest cache directory here to indicate the step ran
        ctx = HermesContext()
        ctx.prepare_step('harvest')

        cmd_entity = self.prov_doc.make_node('Entity', self.prov.hermes_command(self, self.app_entity))
        cmd_entity.commit()

        for plugin_name in self.settings.sources:
            plugin_cls = self.plugins[plugin_name]
            plugin_doc, plugin_activity = self.prov_doc.push(
                self.prov.hermes_plugin_run(plugin_cls.pluing_node, cmd_entity))

            try:
                with plugin_activity.timer:
                    # Load plugin and run the harvester
                    plugin_func = plugin_cls(plugin_doc)
                    harvested_data = plugin_func(self)
                    plugin_activity.add_related(
                        "prov:generated", "Entity",
                        self.prov.hermes_json_data("codemeta data", harvested_data))

                with ctx[plugin_name] as plugin_ctx:
                    plugin_ctx["codemeta"] = harvested_data.compact()
                    plugin_ctx["context"] = {"@context": harvested_data.full_context}

                    plugin_ctx["expanded"] = harvested_data.ld_value

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
                self.errors.append(e)

            finally:
                plugin_activity.commit()
                plugin_doc.finish()

        with ctx["result"] as all_ctx:
            all_ctx["prov"] = self.prov_doc.compact()

        ctx.finalize_step('harvest')
