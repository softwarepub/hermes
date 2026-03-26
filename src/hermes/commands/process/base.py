# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
from typing import Union

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError
from hermes.model.api import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict


class HermesProcessPlugin(HermesPlugin):
    """ Base plugin that defines additional merge strategies."""

    def __call__(self, command: HermesCommand) -> dict[Union[str, None], dict[Union[str, None], MergeAction]]:
        pass


class ProcessSettings(BaseModel):
    """Generic deposition settings."""

    sources: list = []
    plugins: list = ["codemeta"]


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"
    settings_class = ProcessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Metadata processing")
        self.args = args
        merged_doc = ld_merge_dict([{}])

        self.log.info("## Load and run the plugins")
        any_strategies_loaded = False
        # add the strategies from the plugins
        for plugin_name in reversed(self.settings.plugins):
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func = self.plugins[plugin_name]()
            except KeyError:
                self.log.warning(f"Plugin {plugin_name} not found, skipping it now.")
                continue

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                additional_strategies = plugin_func(self)
            except Exception:
                self.log.warning(f"Unknown error while executing the {plugin_name} plugin, skipping it now.")
                continue

            self.log.info(f"### Add the strategies to the merge document {plugin_name} plugin")
            # add strategies to the merge document
            merged_doc.add_strategy(additional_strategies)
            any_strategies_loaded = True

        if not any_strategies_loaded:
            self.log.error("No process plugin was ran successfully.")
            raise RuntimeError("No process plugin was ran successfully.")

        ctx = HermesContext()
        ctx.prepare_step('harvest')

        self.log.info("## Merge the metadata of the harvesters")
        # Get all harvesters
        harvester_names = self.settings.sources if self.settings.sources else self.root_settings.harvest.sources
        merged_any = False
        for harvester in harvester_names:
            self.log.info(f"## Load data from {harvester} plugin")
            # load data from harvester
            try:
                metadata = SoftwareMetadata.load_from_cache(ctx, harvester)
            except Exception:
                # skip this harvester when the data is invalid
                self.log.warning(f"The data from the harvester {harvester} could not be loaded or is invalid.")
                self.log.info(f"## Aborting merge for {harvester}")
                continue

            self.log.info(f"## Merge data from {harvester} plugin")
            # merge data into the merge dict
            try:
                merged_doc.update(metadata)
            except Exception as e:
                self.log.error(f"Merging the data from {harvester} plugin resulted in an error.")
                raise HermesPluginRunError(f"Merging the data from {harvester} plugin failed.") from e
            merged_any = True

        # error if nothing was merged
        if harvester_names and not merged_any:
            self.log.error(
                f"""No metadata has been merged. {
                    "No harvesters to merge from were supplied" if not harvester_names else
                    "The merging failed for all harvesters."
                }"""
            )
            raise RuntimeError("No metadata has been merged.")

        self.log.info("## Store processed metadata")
        # store processed data
        ctx.prepare_step("process")
        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = {"@context": merged_doc.full_context}
            result_ctx["expanded"] = merged_doc.ld_value
        ctx.finalize_step("process")

        ctx.finalize_step("harvest")
