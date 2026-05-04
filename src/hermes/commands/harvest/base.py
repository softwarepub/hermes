# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model import SoftwareMetadata
from hermes.model.provenance.ld_prov import ld_prov_list, ld_prov_node
from hermes.model.types.ld_context import ALL_CONTEXTS


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """
    def __init__(self):
        self.io_operations: list[tuple[dict, dict, dict]] = []
        super().__init__()

    def __call__(self, command: HermesCommand) -> SoftwareMetadata:
        pass

    def load():
        pass

    def write():
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.log.info("# Load provenance from old harvest or create new document.")
        prov_doc, base_plugin = self.init_provenance_document()

        self.log.info("# Metadata harvesting")
        if len(self.settings.sources) == 0:
            self.log.critical("# No harvest plugin was configured to be run and loaded.")
            raise MisconfigurationError("No harvest plugin was configured to be run and loaded.")

        # Initialize the harvest cache directory here to indicate the step ran
        ctx = HermesContext()
        ctx.prepare_step('harvest')

        self.log.info("## Load and run the plugins")
        harvested_any = False
        for plugin_name in self.settings.sources:
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
                harvested_data = plugin_func(self)
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin, skipping it now.")
                continue
            self.remove_provenance_info_for_plugin(prov_doc, plugin_name)

            plugin = prov_doc.add_hermes_plugin("harvest", plugin_name)
            plugin_io_operations = plugin_func.io_operations # liste von drei Tupeln (input_file, load_function, output)
            for plugin_io_operation in plugin_io_operations:
                loaded_source = prov_doc.add_entity()
                loaded_source.update(plugin_io_operation[0])
                io_op = prov_doc.add_activity()
                plugin_io_operation[1]["prov:wasAssociatedWith"] = [base_plugin.ref, plugin.ref]
                plugin_io_operation[1]["prov:used"] = loaded_source.ref
                io_op.update(plugin_io_operation[1])
                loaded_data = prov_doc.add_entity()
                plugin_io_operation[2].update({
                    "prov:wasAttributedTo": plugin.ref,
                    "prov:wasDerivedFrom": loaded_source.ref,
                    "prov:wasGeneratedBy": io_op.ref
                })
                loaded_data.update(plugin_io_operations[2])

            self.log.info(f"### Store metadata harvested by {plugin_name} plugin")
            # store harvested data
            harvested_data.write_to_cache(ctx, plugin_name)
            harvested_any = True

        ctx.finalize_step('harvest')
        if not harvested_any:
            self.log.critical("No harvest plugin ran successfully.")
            raise HermesPluginRunError("No harvest plugin ran successfully.")

    def init_provenance_document(self) -> tuple[ld_prov_list, ld_prov_node]:
        ctx = HermesContext()
        ctx.prepare_step("harvest")
        with ctx["provenance"] as cache:
            try:
                ld_prov_doc = ld_prov_list.from_list(cache["codemeta"], container_type="@graph", context=ALL_CONTEXTS)
                return ld_prov_doc, ld_prov_doc.shallow_search({"schema:name": lambda doc, node: node["schema:name"][0].find("harvest base plugin") != -1})[0]
            except KeyError:
                pass
        prov_doc = ld_prov_list()
        prov_doc.init_hermes_agents()
        return prov_doc, prov_doc.add_hermes_base_plugin("harvest")

    def remove_provenance_info_for_plugin(self, prov_doc, plugin) -> None:
        plugin = prov_doc.shallow_search({
            "schema:name": (lambda doc, node: f"harvest plugin {plugin}" in node["schema:name"]),
        })
        if len(plugin) == 0:
            return
        # two passes are needed because the nodes are nested exactly two levels
        related = prov_doc.shallow_search({
            "prov:wasAssociatedWith": (lambda doc, node: plugin.ref in node["prov:wasAssociatedWith"]),
            "prov:wasAttributedTo": (lambda doc, node: plugin.ref in node["prov:wasAttributedTo"])
        })
        ids = [plugin.ref, *(rel.ref for rel in related)]
        related = prov_doc.shallow_search({
            f"prov:{key}": (lambda doc, node: any(id in node[f"prov:{key}"] for id in ids)) for key in [
                "wasAssociatedWith", "wasAttributedTo", "wasGeneratedBy", "used", "wasDerivedFrom", "wasInformedBy"
            ]
        })
        for item in related:
            items = prov_doc.shallow_search({"@id": (lambda doc, node: node["@id"] == item["@id"])})
            del prov_doc[items[0].index]
