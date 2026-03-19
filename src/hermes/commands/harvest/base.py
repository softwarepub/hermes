# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError
from hermes.model import SoftwareMetadata


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> SoftwareMetadata:
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Metadata harvesting")
        self.args = args

        # Initialize the harvest cache directory here to indicate the step ran
        ctx = HermesContext()
        ctx.prepare_step('harvest')

        self.log.info("## Load and run the plugins")
        for plugin_name in self.settings.sources:
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func = self.plugins[plugin_name]()
            except KeyError as e:
                self.log.error(f"Plugin {plugin_name} not found.")
                raise MisconfigurationError(f"Harvest plugin {plugin_name} not found.")

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                harvested_data = plugin_func(self)
            except Exception as e:
                self.log.error(f"Unknown error while executing the {plugin_name} plugin.")
                raise HermesPluginRunError(
                    f"Something went wrong while running the harvest plugin {plugin_name}"
                ) from e

            self.log.info(f"### Store metadata harvested by {plugin_name} plugin")
            # store harvested data
            harvested_data.write_to_cache(ctx, plugin_name)

        ctx.finalize_step('harvest')
