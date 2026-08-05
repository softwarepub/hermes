# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import datetime
from typing import Optional

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesCuratePlugin(HermesPlugin):
    """ Base plugin for curate plugins. """

    def __call__(self, command: HermesCommand, metadata: SoftwareMetadata) -> SoftwareMetadata:
        pass


class CurateSettings(BaseModel):
    """Generic deposition settings."""

    plugin: str = "pass_curate"


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"
    settings_class = CurateSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.log.info("# Load provenance data from process step")
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            prov_doc.add_hermes_settings(self)
            prov_doc.add_settings_to_command("curate", self)
            curate_command = prov_doc.get_hermes_command("curate")
            curate_base_plugin = prov_doc.get_hermes_base_plugin("curate")
            process_command = prov_doc.get_hermes_command("process")
            hermes_cache = prov_doc.get_hermes_cache()

        self.log.info("# Metadata curation")
        plugin_name = self.settings.plugin

        ctx = HermesContext()
        ctx.prepare_step("curate")

        self.log.info("## Load processed metadata")
        # load processed data
        ctx.prepare_step("process")
        try:
            begin_load_at_time = datetime.datetime.now().isoformat()
            metadata = SoftwareMetadata.load_from_cache(ctx, "result")
            end_load_at_time = datetime.datetime.now().isoformat()
        except Exception as e:
            self.log.critical(
                "## The data from the process step could not be loaded or is invalid for some reason.",
                exc_info=1
            )
            raise HermesValidationError("The results of the process step are invalid.") from e
        ctx.finalize_step("process")

        # save loaded metadata now, because it could be altered in curation
        loaded_metadata_str = str(metadata.compact())

        self.log.info(f"## Load curation plugin {plugin_name}")
        # load plugin
        try:
            plugin_func = self.plugins[plugin_name]()
        except KeyError:
            self.log.error(f"## Curate plugin {plugin_name} not found.")
            raise MisconfigurationError(f"Curate plugin {plugin_name} not found.")

        self.log.info(f"## Run curation plugin {plugin_name}")
        # run plugin
        try:
            curated_metadata = plugin_func(self, metadata)
            end_curation_time = datetime.datetime.now().isoformat()
        except Exception as e:
            self.log.critical(f"## Unknown error while executing the {plugin_name} plugin.", exc_info=1)
            raise HermesPluginRunError(f"Something went wrong while running the curate plugin {plugin_name}") from e

        self.log.info("## Store curated data")
        # store metadata
        begin_store_at_time = datetime.datetime.now().isoformat()
        curated_metadata.write_to_cache(ctx, "result")
        stored_at_time = datetime.datetime.now().isoformat()

        if prov_doc is not None:
            curate_plugin = prov_doc.add_hermes_plugin("curate", plugin_name, plugin_func, self)
            store_action_of_process = prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and
                node["prov:wasAssociatedWith"] == [process_command.ref, hermes_cache.ref] and
                "prov:wasInformedBy" in node
            ))[0]
            stored_results_of_process = [res.ref for res in prov_doc.shallow_search(lambda node: (
                "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action_of_process.ref]
            ))]
            load_action = prov_doc.add_activity(data={
                "schema:description": "loads the data from process step",
                "prov:wasAssociatedWith": [process_command.ref, hermes_cache.ref],
                "prov:used": stored_results_of_process,
                "prov:startedAtTime": begin_load_at_time,
                "prov:endedAtTime": end_load_at_time
            })
            loaded_data = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "data loaded from process step",
                "schema:text": loaded_metadata_str,  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:wasGeneratedBy": load_action.ref,
                "prov:wasDerivedFrom": stored_results_of_process,
                "prov:generatedAtTime": end_load_at_time
            })
            curated_data = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "curated metadata",
                "schema:text": str(curated_metadata.compact()),  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": [curate_plugin.ref, curate_base_plugin.ref, curate_command.ref],
                "prov:wasInfluencedBy": curate_plugin.ref,
                "prov:wasGeneratedBy": load_action.ref,
                "prov:wasDerivedFrom": loaded_data.ref,
                "prov:generatedAtTime": end_curation_time
            })
            write = prov_doc.add_activity(data={
                "schema:description": "Writes the processed metadata into the HERMES cache.",
                "prov:wasAssociatedWith": [curate_command.ref, hermes_cache.ref],
                "prov:used": curated_data.ref,
                "prov:startedAtTime": begin_store_at_time,
                "prov:endedAtTime": stored_at_time
            })
            # TODO: add more info
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The compacted version of the processed metadata.",
                "schema:text": str(curated_metadata.compact()),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "curate" / "result" / "codemeta.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": curated_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The context of the processed metadata.",
                "schema:text": str({"@context": curated_metadata.full_context}),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "curate" / "result" / "context.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": curated_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The expanded version of the processed metadata.",
                "schema:text": str(curated_metadata.ld_value),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "curate" / "result" / "expanded.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": curated_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": stored_at_time
            })

            with ctx["provenance"] as cache:
                cache["result"] = prov_doc.ld_value

        ctx.finalize_step("curate")

    def load_prov_doc(self) -> Optional[ld_prov_list]:
        ctx = HermesContext()
        ctx.prepare_step("process")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except Exception:
                self.log.warning(
                    "The provenance data from the process step could not be loaded. "
                    "Processing will proceed without collecting provenance data.",
                    exc_info=1
                )
            finally:
                ctx.finalize_step("process")
