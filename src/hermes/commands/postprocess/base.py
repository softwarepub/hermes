# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError


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

        if not plugin_names:
            self.log.warning("# No plugin was configured to be run yet the postprocess command was executed.")
            return

        self.log.info("## Load and run the plugins")
        ran_any = False
        for plugin_name in plugin_names:
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func = self.plugins[plugin_name]()
            except KeyError:
                self.log.error(f"### Plugin {plugin_name} not found.")
                continue

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                plugin_func(self)
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin.")
                continue

            ran_any = True

        if not ran_any:
            self.log.critical("## No postprocess plugin ran successfully.")
            raise HermesPluginRunError("No postprocess plugin ran successfully.")
