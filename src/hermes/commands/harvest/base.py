# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import datetime
from io import IOBase
from pathlib import Path

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model import SoftwareMetadata
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """
    def __init__(self):
        self.io_operations: list[tuple[dict, dict, dict]] = []
        super().__init__()

    def __call__(self, command: HermesCommand) -> SoftwareMetadata:
        pass

    def load(self, func, source, *args, **kwargs):
        source_metadata = {"schema:description": "metadata source"}
        if isinstance(source, IOBase):
            source_metadata["schema:url"] = Path(source.name).absolute().as_uri()
        elif isinstance(source, Path):
            source_metadata["schema:url"] = source.absolute().as_uri()
        elif isinstance(source, str):
            source_metadata["schema:url"] = Path(source).absolute().as_uri()
        io_operation = {
            "schema:description": "Load operation called with ("
            f"{source_metadata['schema:url'] if 'schema:url' in source_metadata else str(source)}"
            f"{', ' + str(args) if args else ''}{', ' + str(kwargs) if kwargs else ''}).",
            "schema:name": f"{func.__module__}.{func.__qualname__}"
        }
        result = func(source, *args, **kwargs)
        loaded_metadata = {"schema:description": "the loaded data", "schema:text": str(result)}
        self.io_operations.append((source_metadata, io_operation, loaded_metadata))
        return result

    def write():
        # TODO: Implement
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


def remove_harvest_plugin_from_prov_doc(prov_doc: ld_prov_list, plugin: str) -> None:
    plugin = prov_doc.get_hermes_plugin("harvest", plugin)
    if plugin is None:
        return
    related = prov_doc.shallow_search(lambda node: (
        ("prov:wasAssociatedWith" in node and plugin.ref in node["prov:wasAssociatedWith"]) or
        ("prov:wasAttributedTo" in node and plugin.ref in node["prov:wasAttributedTo"])
    ))
    if len(related) == 0:
        del prov_doc[plugin.index]
        return
    ids = [plugin.ref, *(rel.ref for rel in related)]
    used_entities = [rel["prov:used"][0]["@id"] for rel in related if "prov:used" in rel]
    related = prov_doc.shallow_search(lambda node: node["@id"] in used_entities)
    related += prov_doc.shallow_search(lambda node: any(
        (f"prov:{key}" in node and id in node[f"prov:{key}"]) for id in ids for key in [
            "wasAssociatedWith", "wasAttributedTo", "wasGeneratedBy", "used", "wasDerivedFrom", "wasInformedBy"
        ]
    ))
    del prov_doc[plugin.index]
    for item in related:
        items = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == item["@id"]))
        if len(items) == 1:
            del prov_doc[items[0].index]


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.log.info("# Load provenance from old harvest or create new document.")
        prov_doc = self.init_provenance_document()
        base_plugin = prov_doc.get_hermes_base_plugin("harvest")

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
                harvested_data: SoftwareMetadata = plugin_func(self)
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin, skipping it now.")
                continue
            returned_at_time = datetime.datetime.now().isoformat()

            self.log.info(f"### Store metadata harvested by {plugin_name} plugin")
            # store harvested data
            begin_store_at_time = datetime.datetime.now().isoformat()
            harvested_data.write_to_cache(ctx, plugin_name)
            stored_at_time = datetime.datetime.now().isoformat()
            harvested_any = True

            remove_harvest_plugin_from_prov_doc(prov_doc, plugin_name)

            plugin = prov_doc.add_hermes_plugin("harvest", plugin_name)
            plugin_io_operations = plugin_func.io_operations
            outputs = []
            io_ops = []
            for plugin_io_operation in plugin_io_operations:
                loaded_source = prov_doc.add_entity(data=plugin_io_operation[0])
                plugin_io_operation[1].update(
                    {"prov:wasAssociatedWith": [base_plugin.ref, plugin.ref], "prov:used": loaded_source.ref}
                )
                io_op = prov_doc.add_activity(data=plugin_io_operation[1])
                plugin_io_operation[2].update({
                    "prov:wasAttributedTo": plugin.ref,
                    "prov:wasDerivedFrom": loaded_source.ref,
                    "prov:wasGeneratedBy": io_op.ref
                })
                loaded_data = prov_doc.add_entity(data=plugin_io_operation[2])
                outputs.append(loaded_data.ref)
                io_ops.append(io_op.ref)

            map_activity = prov_doc.add_activity(data={
                "schema:description": "Maps the loaded data to the JSON-LD contexts vocabulary.",
                "prov:wasInformedBy": io_ops,
                "prov:used": outputs,
                "prov:wasAssociatedWith": plugin.ref,
                "prov:startedAtTime": returned_at_time
            })
            data_output = prov_doc.add_entity(data={
                "schema:description": "the harvested metadata",
                "prov:wasAttributedTo": plugin.ref,
                "prov:wasGeneratedBy": map_activity.ref,
                "prov:wasDerivedFrom": outputs,
                "prov:generatedAtTime": returned_at_time
            })

            write = prov_doc.add_activity(data={
                "schema:description": "Writes the harvested metadata into the HERMES cache.",
                "prov:wasAssociatedWith": [
                    prov_doc.get_hermes_command("harvest").ref,
                    prov_doc.get_hermes_cache().ref,
                    plugin.ref
                ],
                "prov:used": data_output.ref,
                "prov:wasInformedBy": map_activity.ref,
                "prov:startedAtTime": begin_store_at_time,
                "prov:endedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The compacted version of the harvested metadata.",
                "schema:text": str(harvested_data.compact()),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "harvest" / plugin_name / "codemeta.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": data_output.ref,
                "prov:wasAttributedTo": prov_doc.get_hermes_cache().ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The context of the harvested metadata.",
                "schema:text": str({"@context": harvested_data.full_context}),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "harvest" / plugin_name / "context.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": data_output.ref,
                "prov:wasAttributedTo": prov_doc.get_hermes_cache().ref,
                "prov:generatedAtTime": stored_at_time
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The expanded version of the harvested metadata.",
                "schema:text": str(harvested_data.ld_value),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (ctx.cache_dir / "harvest" / plugin_name / "expanded.json").absolute().as_uri(),
                "prov:wasGeneratedBy": write.ref,
                "prov:wasDerivedFrom": data_output.ref,
                "prov:wasAttributedTo": prov_doc.get_hermes_cache().ref,
                "prov:generatedAtTime": stored_at_time
            })

        with ctx["provenance"] as cache:
            cache["result"] = prov_doc.ld_value

        ctx.finalize_step('harvest')
        if not harvested_any:
            self.log.critical("No harvest plugin ran successfully.")
            raise HermesPluginRunError("No harvest plugin ran successfully.")

    def init_provenance_document(self) -> ld_prov_list:
        ctx = HermesContext()
        ctx.prepare_step("harvest")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                pass
        prov_doc = ld_prov_list()
        prov_doc.init_hermes_agents()
        return prov_doc
