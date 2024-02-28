# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0
import abc
# SPDX-FileContributor: Michael Meinel

import argparse

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.settings import HarvestSettings


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """
    def __call__(self, command: HermesCommand) -> None:
        pass


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]
                plugin_func(self)

            except KeyError:
                self.log.error("Plugin %s not found.", plugin_name)

            except TypeError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
