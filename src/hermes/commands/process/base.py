# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
from typing import Union

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.api import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict


class HermesProcessPlugin(HermesPlugin):
    """ Base plugin that defines additional merge strategies."""

    def __call__(self, command: HermesCommand) -> dict[Union[str, None], dict[Union[str, None], MergeAction]]:
        pass


class ProcessSettings(BaseModel):
    """Generic deposition settings."""

    plugins: list = []


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"
    settings_class = ProcessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Metadata processing")
        self.args = args
        merged_doc = ld_merge_dict([{}])

        self.log.info("## Load and run the plugins")
        # add the strategies from the plugins
        for plugin_name in reversed(self.settings.plugins):
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
                additional_strategies = plugin_func(self)
            except Exception as e:
                self.log.error(f"Unknown error while executing the {plugin_name} plugin.")
                raise HermesPluginRunError(
                    f"Something went wrong while running the postprocess plugin {plugin_name}"
                ) from e

            self.log.info(f"### Add the strategies to the merge document {plugin_name} plugin")
            # add strategies to the merge document
            merged_doc.add_strategy(additional_strategies)

        ctx = HermesContext()
        ctx.prepare_step('harvest')

        self.log.info("## Merge the metadata of the harvesters")
        # Get all harvesters
        harvester_names = self.root_settings.harvest.sources
        for harvester in harvester_names:
            self.log.info(f"## Load data from {harvester} plugin")
            # load data from harvester
            try:
                metadata = SoftwareMetadata.load_from_cache(ctx, harvester)
            except Exception as e:
                self.log.error(f"The data from the harvester {harvester} could not be loaded or is invalid.")
                raise HermesValidationError(f"The results of the harvest plugin {harvester} is invalid.") from e

            self.log.info(f"## Merge data from {harvester} plugin")
            # merge data into the merge dict
            merged_doc.update(metadata)

        self.log.info("## Store processed metadata")
        # store processed data
        ctx.prepare_step("process")
        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = {"@context": merged_doc.full_context}
            result_ctx["expanded"] = merged_doc.ld_value
        ctx.finalize_step("process")

        ctx.finalize_step("harvest")
