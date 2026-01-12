# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError
from hermes.model import SoftwareMetadata


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> tuple[SoftwareMetadata, dict]:
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

        for plugin_name in self.settings.sources:
            plugin_cls = self.plugins[plugin_name]

            try:
                # Load plugin and run the harvester
                plugin_func = plugin_cls()
                harvested_data = plugin_func(self)

                with ctx[plugin_name] as plugin_ctx:
                    plugin_ctx["codemeta"] = harvested_data.compact()
                    plugin_ctx["context"] = {"@context": harvested_data.full_context}

                    plugin_ctx["expanded"] = harvested_data.ld_value

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
                self.errors.append(e)

        ctx.finalize_step('harvest')
