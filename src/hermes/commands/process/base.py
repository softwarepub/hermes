# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
from typing import Optional

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.api import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesProcessPlugin(HermesPlugin):
    """ Base plugin that defines additional merge strategies."""

    def __call__(self, command: HermesCommand) -> dict[Optional[str], dict[Optional[str], MergeAction]]:
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
        self.log.info("# Load provenance data from harvest step")
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            process_command = prov_doc.get_hermes_command("process")
            hermes_cache = prov_doc.get_hermes_cache()

        self.log.info("# Metadata processing")
        merged_doc = ld_merge_dict([{}])

        if not self.settings.plugins:
            self.log.critical(
                "# It was explicitly configured that no process plugin should be used."
                " Hint: Do not configure anything to use standard 'codemeta' plugin."
            )
            raise MisconfigurationError("Explicit configuration to use no process plugin.")

        # Get all harvesters
        harvester_names = self.settings.sources if self.settings.sources else self.root_settings.harvest.sources
        if not harvester_names:
            self.log.critical("# No harvesters to merge from were configured.")
            raise MisconfigurationError("No harvesters to merge from were configured.")

        self.log.info("## Load and run the plugins")
        any_strategies_loaded = False
        strategy_action, merged_strategies = None, None
        # add the strategies from the plugins
        for plugin_name in reversed(self.settings.plugins):
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func = self.plugins[plugin_name]()
            except KeyError:
                self.log.error(f"### Plugin {plugin_name} not found, skipping it now.")
                continue

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                additional_strategies = plugin_func(self)
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin, skipping it now.")
                continue

            self.log.info(f"### Add the strategies to the merge document {plugin_name} plugin")
            # add strategies to the merge document
            merged_doc.add_strategy(additional_strategies)
            any_strategies_loaded = True

            if prov_doc is None:
                continue
            plugin = prov_doc.add_hermes_plugin("process", plugin_name)
            new_strategy_generation = prov_doc.add_activity(data={"prov:wasAssociatedWith": plugin.ref})
            new_strategies = prov_doc.add_entity(
                data={"prov:wasAttributedTo": plugin.ref, "prov:wasGeneratedBy": new_strategy_generation.ref}
            )
            if merged_strategies is None:
                merged_strategies = new_strategies
                strategy_action = new_strategy_generation
                continue
            strategy_action = prov_doc.add_activity(data={
                "prov:used": [merged_strategies.ref, new_strategies.ref],
                "prov:wasInformedBy": [strategy_action.ref, new_strategy_generation.ref],
                "prov:wasAssociatedWith": process_command.ref
            })
            merged_strategies = prov_doc.add_entity(data={
                "prov:wasDerivedFrom": [merged_strategies.ref, new_strategies.ref],
                "prov:wasGeneratedBy": strategy_action.ref,
                "prov:wasAttributedTo": process_command.ref
            })

        if not any_strategies_loaded:
            self.log.critical("## No process plugin was ran successfully.")
            raise HermesPluginRunError("No process plugin was ran successfully.")

        ctx = HermesContext()
        ctx.prepare_step('harvest')

        # merge data from harvesters
        self.log.info("## Merge the metadata of the harvesters")
        merged_any = False
        merge_action, merged_data = None, None
        for harvester in harvester_names:
            self.log.info(f"### Load data from {harvester} plugin")
            # load data from harvester
            try:
                metadata = SoftwareMetadata.load_from_cache(ctx, harvester)
            except Exception:
                # skip this harvester when the data is invalid
                self.log.exception(
                    f"### The data from the harvester {harvester} could not be loaded or is invalid, skipping it now."
                )
                continue

            self.log.info(f"### Merge data from {harvester} plugin")
            # merge data into the merge dict
            try:
                merged_doc.update(metadata)
            except Exception as e:
                self.log.critical(f"### Merging the data from {harvester} plugin resulted in an error.", exc_info=True)
                raise RuntimeError(f"Merging the data from {harvester} plugin failed.") from e
            merged_any = True

            if prov_doc is None:
                continue
            harvest_plugin = prov_doc.get_hermes_plugin("harvest", harvester)
            harvest_command = prov_doc.get_hermes_command("harvest")
            store_action = prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and
                node["prov:wasAssociatedWith"] == [harvest_plugin.ref, hermes_cache.ref, harvest_command.ref]
            ))[0]
            stored_results = [
                result.ref for result in prov_doc.shallow_search(
                    lambda node: ("prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == store_action.ref)
                )
            ]
            new_data_load = prov_doc.add_activity(data={
                "prov:wasAssociatedWith": [process_command.ref, hermes_cache.ref],
                "prov:used": stored_results
            })
            new_data = prov_doc.add_entity(data={
                "prov:wasAttributedTo": plugin.ref,
                "prov:wasGeneratedBy": new_data_load.ref,
                "prov:wasDerivedFrom": stored_results
            })
            if merged_data is None:
                merged_data = new_data
                merge_action = new_data_load
                continue
            merge_action = prov_doc.add_activity(data={
                "prov:used": [merged_data.ref, new_data.ref, merged_strategies.ref],
                "prov:wasInformedBy": [merge_action.ref, new_data_load.ref],
                "prov:wasAssociatedWith": process_command.ref
            })
            merged_data = prov_doc.add_entity(data={
                "prov:wasDerivedFrom": [merged_data.ref, new_data.ref],
                "prov:wasGeneratedBy": merge_action.ref,
                "prov:wasAttributedTo": process_command.ref
            })

        # error if nothing was merged
        if not merged_any:
            self.log.critical("No metadata has been merged, the loading of the data failed for all harvesters.")
            raise RuntimeError("No metadata has been merged.")

        self.log.info("## Store processed metadata")
        # store processed data
        ctx.prepare_step("process")
        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = {"@context": merged_doc.full_context}
            result_ctx["expanded"] = merged_doc.ld_value

        if prov_doc is not None:
            write = prov_doc.add_activity(data={
                "prov:wasAssociatedWith": [process_command.ref, hermes_cache.ref, plugin.ref],
                "prov:used": merged_data.ref,
                "prov:wasInformedBy": merge_action.ref
            })
            # TODO: add more info
            prov_doc.add_entity(data={
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": merged_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref
            })
            prov_doc.add_entity(data={
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": merged_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref
            })
            prov_doc.add_entity(data={
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": merged_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref
            })

            with ctx["provenance"] as cache:
                cache["result"] = prov_doc.ld_value

        ctx.finalize_step("process")

        ctx.finalize_step("harvest")

    def load_prov_doc(self) -> Optional[ld_prov_list]:
        ctx = HermesContext()
        ctx.prepare_step("harvest")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except Exception:
                self.log.warning(
                    "The provenance data from the harvest step could not be loaded. "
                    "Processing will proceed without collecting provenance data.",
                    exc_info=1
                )
