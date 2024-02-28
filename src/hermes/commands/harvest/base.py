# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0
import abc
# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.errors import HermesValidationError


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> None:
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

        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]()
                harvested_data = plugin_func(self)
                print(harvested_data)
                # TODO: store harvested data for later use

            except KeyError:
                self.log.error("Plugin '%s' not found.", plugin_name)

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
