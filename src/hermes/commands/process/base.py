# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import datetime
from typing import Optional

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.commands.harvest.base import remove_harvest_plugin_from_prov_doc
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
        self.args = args
        self.log.info("# Load provenance data from harvest step")
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            prov_doc.add_hermes_settings(self)
            prov_doc.add_settings_to_command("process", self)
            process_command = prov_doc.get_hermes_command("process")
            hermes_cache = prov_doc.get_hermes_cache()

        self.log.info("# Metadata processing")
        merged_doc = ld_merge_dict([{}], prov_doc)

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
                generate_strategies_start = datetime.datetime.now()
                additional_strategies = plugin_func(self)
                generate_strategies_end = datetime.datetime.now()
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin, skipping it now.")
                continue

            self.log.info(f"### Add the strategies to the merge document {plugin_name} plugin")
            # add strategies to the merge document
            merge_strategies_start = datetime.datetime.now()
            merged_doc.add_strategy(additional_strategies)
            merge_strategies_end = datetime.datetime.now()
            any_strategies_loaded = True

            if prov_doc is None:
                continue
            plugin = prov_doc.add_hermes_plugin("process", plugin_name, plugin_func, self)
            new_strategy_generation = prov_doc.add_activity(data={
                "schema:description": "generate new merge strategies",
                "prov:wasAssociatedWith": plugin.ref,
                "prov:startedAtTime": generate_strategies_start,
                "prov:endedAtTime": generate_strategies_end
            })
            new_strategies = prov_doc.add_entity(data={  # TODO: record strategies
                "@type": "schema:CreativeWork",
                "schema:description": f"new merge strategies of plugin {plugin_name}",
                "schema:text": str(additional_strategies),  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": plugin.ref,
                "prov:wasGeneratedBy": new_strategy_generation.ref,
                "prov:generatedAtTime": generate_strategies_end
            })
            if merged_strategies is None:
                merged_strategies = new_strategies
                strategy_action = new_strategy_generation
                continue
            strategy_action = prov_doc.add_activity(data={
                "schema:description": "merging the new strategies into the others",
                "prov:used": [merged_strategies.ref, new_strategies.ref],
                "prov:wasInformedBy": [strategy_action.ref, new_strategy_generation.ref],
                "prov:wasAssociatedWith": process_command.ref,
                "prov:startedAtTime": merge_strategies_start,
                "prov:endedAtTime": merge_strategies_end
            })
            merged_strategies = prov_doc.add_entity(data={  # TODO: record strategies
                "schema:description": "the merge strategies of multiple plugins merged together",
                "schema:text": str(merged_doc.strategies),  # TODO: maybe "prov:value" instead?
                "prov:wasDerivedFrom": [merged_strategies.ref, new_strategies.ref],
                "prov:wasGeneratedBy": strategy_action.ref,
                "prov:wasAttributedTo": process_command.ref,
                "prov:generatedAtTime": merge_strategies_end
            })

        if not any_strategies_loaded:
            self.log.critical("## No process plugin was ran successfully.")
            raise HermesPluginRunError("No process plugin was ran successfully.")

        ctx = HermesContext()
        ctx.prepare_step('harvest')

        # merge data from harvesters
        self.log.info("## Merge the metadata of the harvesters")
        merged_any = False
        for harvester in harvester_names:
            self.log.info(f"### Load data from {harvester} plugin")
            # load data from harvester
            try:
                load_start = datetime.datetime.now()
                metadata = SoftwareMetadata.load_from_cache(ctx, harvester)
                load_end = datetime.datetime.now()
            except Exception:
                # skip this harvester when the data is invalid
                if prov_doc is not None:
                    remove_harvest_plugin_from_prov_doc(prov_doc, harvester)
                self.log.exception(
                    f"### The data from the harvester {harvester} could not be loaded or is invalid, skipping it now."
                )
                continue

            if prov_doc is not None:
                harvest_plugin = prov_doc.get_hermes_plugin("harvest", harvester)
                harvest_command = prov_doc.get_hermes_command("harvest")
                store_action = prov_doc.shallow_search(lambda node: (
                    "prov:wasAssociatedWith" in node and
                    node["prov:wasAssociatedWith"] == [harvest_plugin.ref, hermes_cache.ref, harvest_command.ref]
                ))[0]
                stored_results = [
                    result.ref for result in prov_doc.shallow_search(lambda node: (
                        "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action.ref]
                    ))
                ]
                new_action = prov_doc.add_activity(data={  # load of new data
                    "schema:description": f"loads the data from {harvester} plugin",
                    "prov:wasAssociatedWith": [process_command.ref, hermes_cache.ref],
                    "prov:used": stored_results,
                    "prov:startedAtTime": load_start,
                    "prov:endedAtTime": load_end
                })
                new_data = prov_doc.add_entity(data={  # new data to be merged
                    "@type": "schema:CreativeWork",
                    "schema:description": f"data loaded from {harvester} plugin",
                    "schema:text": str(metadata.compact()),  # TODO: maybe "prov:value" instead?
                    "prov:wasAttributedTo": [process_command.ref, hermes_cache.ref],
                    "prov:wasGeneratedBy": new_action.ref,
                    "prov:wasDerivedFrom": stored_results,
                    "prov:generatedAtTime": load_end
                })
                if merged_any:
                    # One pass must have been completed already.
                    new_action = prov_doc.add_activity(data={
                        "schema:description": "merges the old data object with the new data",
                        "prov:used": [last_data.ref, new_data.ref],
                        "prov:wasInformedBy": [last_action.ref, new_action.ref],
                        "prov:wasAssociatedWith": process_command.ref
                    })  # initial merge action of the merge
                    merged_doc.prov_objects = [new_action, new_data, last_data]  # set the starting objects of the merge

            self.log.info(f"### Merge data from {harvester} plugin")
            # merge data into the merge dict
            try:
                merge_start = datetime.datetime.now()
                merged_doc.update(metadata)
                merge_end = datetime.datetime.now()
            except Exception as e:
                # TODO: Maybe this state is recoverable by starting over again and skipping this plugin.
                self.log.critical(f"### Merging the data from {harvester} plugin resulted in an error.", exc_info=True)
                raise RuntimeError(f"Merging the data from {harvester} plugin failed.") from e

            if prov_doc is not None:
                if merged_any:
                    new_action["prov:startedAtTime"] = merge_start
                    new_action["prov:endedAtTime"] = merge_end
                last_action = merged_doc.prov_objects[0] if merged_any else new_action
                last_data = merged_doc.prov_objects[2] if merged_any else new_data
            merged_any = True

        # error if nothing was merged
        if not merged_any:
            self.log.critical("No metadata has been merged, the loading of the data failed for all harvesters.")
            raise RuntimeError("No metadata has been merged.")

        self.log.info("## Store processed metadata")
        # store processed data
        ctx.prepare_step("process")
        begin_store_at_time = datetime.datetime.now()
        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = {"@context": merged_doc.full_context}
            result_ctx["expanded"] = merged_doc.ld_value
        stored_at_time = datetime.datetime.now()

        if prov_doc is not None:
            write = prov_doc.add_activity(data={
                "schema:description": "Writes the processed metadata into the HERMES cache.",
                "prov:wasAssociatedWith": [process_command.ref, hermes_cache.ref],
                "prov:used": last_data.ref,
                "prov:wasInformedBy": last_action.ref,
                "prov:startedAtTime": begin_store_at_time,
                "prov:endedAtTime": stored_at_time
            })
            # TODO: add more info
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The compacted version of the processed metadata.",
                "schema:text": str(merged_doc.compact()),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "process" / "result" / "codemeta.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": last_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The context of the processed metadata.",
                "schema:text": str({"@context": merged_doc.full_context}),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "process" / "result" / "context.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": last_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The expanded version of the processed metadata.",
                "schema:text": str(merged_doc.ld_value),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "process" / "result" / "expanded.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": last_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
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
            finally:
                ctx.finalize_step("harvest")
