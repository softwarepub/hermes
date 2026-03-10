# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin


class HermesPostprocessPlugin(HermesPlugin):
    pass


class PostprocessSettings(BaseModel):
    """Generic post-processing settings."""

    run: list = []


class HermesPostprocessCommand(HermesCommand):
    """Post-process the published metadata after deposition."""

    command_name = "postprocess"
    settings_class = PostprocessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        plugin_names = self.settings.run

        for plugin_name in plugin_names:
            try:
                plugin_func = self.plugins[plugin_name]()
                plugin_func(self)
            except KeyError as e:
                self.log.error("Plugin '%s' not found.", plugin_name)
                self.errors.append(e)
