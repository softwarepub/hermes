# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError


class HermesCuratePlugin(HermesPlugin):
    """ Base plugin for curate plugins. """

    def __call__(self, command: HermesCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        pass


class CurateSettings(BaseModel):
    """Generic deposition settings."""

    plugin: str = ""


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"
    settings_class = CurateSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Metadata curation")
        plugin_name = self.settings.plugin

        ctx = HermesContext()
        ctx.prepare_step("curate")

        self.log.info("## Load processed metadata")
        # load processed data
        ctx.prepare_step("process")
        try:
            metadata = SoftwareMetadata.load_from_cache(ctx, "result")
        except Exception as e:
            self.log.error("The data from the process step could not be loaded or is invalid for some reason.")
            raise HermesValidationError("The results of the process step are invalid.") from e
        ctx.finalize_step("process")

        self.log.info("## Load curation plugin")
        # load plugin
        try:
            plugin_func = self.plugins[plugin_name]()
        except KeyError:
            self.log.error(f"Plugin {plugin_name} not found.")
            raise MisconfigurationError(f"Curate plugin {plugin_name} not found.")

        self.log.info("## Run curation plugin")
        # run plugin
        try:
            curated_metadata = plugin_func(self, metadata)
        except Exception as e:
            self.log.error(f"Unknown error while executing the {plugin_name} plugin.")
            raise HermesPluginRunError(f"Something went wrong while running the curate plugin {plugin_name}") from e

        self.log.info("## Store curated data")
        # store metadata
        curated_metadata.write_to_cache(ctx, "result")

        ctx.finalize_step("curate")
