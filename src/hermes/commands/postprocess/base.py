# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError


class HermesPostprocessPlugin(HermesPlugin):
    """ Base plugin for postprocess plugins. """

    def __call__(self, command: HermesCommand) -> None:
        pass


class PostprocessSettings(BaseModel):
    """Generic post-processing settings."""

    run: list = []


class HermesPostprocessCommand(HermesCommand):
    """Post-process the published metadata after deposition."""

    command_name = "postprocess"
    settings_class = PostprocessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Postprocessing")
        self.args = args
        plugin_names = self.settings.run

        self.log.info("## Load and run the plugins")
        for plugin_name in plugin_names:
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func = self.plugins[plugin_name]()
            except KeyError as e:
                self.log.error(f"Plugin {plugin_name} not found.")
                raise MisconfigurationError(f"Postprocess plugin {plugin_name} not found.")

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                plugin_func(self)
            except Exception as e:
                self.log.error(f"Unknown error while executing the {plugin_name} plugin.")
                raise HermesPluginRunError(
                    f"Something went wrong while running the postprocess plugin {plugin_name}"
                ) from e
