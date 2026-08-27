# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

import argparse
import datetime
from io import IOBase
from pathlib import Path
from typing import Any, Callable, Optional
from typing_extensions import Self

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model import SoftwareMetadata
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    Attributes:
        operations (list[tuple[dict[str, str], dict[str, str], dict[str, str]]]): The information recorded on the
            load operations executed by the plugin.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __init__(self: Self) -> None:
        """
        Create a new instance of a HermesHarvestPlugin.

        Returns:
            None:
        """
        self.operations: list[tuple[dict[str, str], dict[str, str], dict[str, str]]] = []
        super().__init__()

    def __call__(self: Self, command: "HermesHarvestCommand") -> SoftwareMetadata:
        """
        Execute the hermes harvest plugin `self`.

        Args:
            command (HermesHarvestCommand): The command being executed.

        Returns:
            SoftwareMetadata: The harvested metadata.
        """
        pass

    def load(self: Self, func: Callable, source: Any, *args: Optional[Any], **kwargs: Optional[Any]) -> Any:
        """
        Load some data from some source using some function so that the calls provenance information is recorded.

        `func(source, *args, **kwargs)` will be executed.

        Args:
            func (Callable): The function used for loading the requested source.
            source (Any): The source the data is to be loaded from.
            args (Any | None): Additional positional arguments for the load.
            kwargs (Any | None): Additional keyword arguments for the load.

        Returns:
            Any: The result of the load operation.
        """
        # collect basic metadata
        source_metadata = {"schema:description": "metadata source"}
        if isinstance(source, IOBase):
            source_metadata["schema:url"] = Path(source.name).absolute().as_uri()
        elif isinstance(source, Path):
            source_metadata["schema:url"] = source.absolute().as_uri()
        elif isinstance(source, str):
            try:
                source_metadata["schema:url"] = Path(source).absolute().as_uri()
            except Exception:
                source_metadata["schema:url"] = source
        operation = {
            "schema:description": "Load operation called with ("
            f"{source_metadata['schema:url'] if 'schema:url' in source_metadata else str(source)}"
            f"{', ' + str(args) if args else ''}{', ' + str(kwargs) if kwargs else ''}).",
            "schema:name": f"{func.__module__}.{func.__qualname__}"
        }
        operation["prov:startedAtTime"] = datetime.datetime.now()
        # execute the load operation
        result = func(source, *args, **kwargs)
        # complete metadata collection
        operation["prov:endedAtTime"] = datetime.datetime.now()
        loaded_metadata = {"schema:description": "the loaded data", "schema:text": str(result)}
        # store metadata
        self.operations.append((source_metadata, operation, loaded_metadata))
        # return result of the load operation
        return result


class HarvestSettings(BaseModel):
    """
    Generic harvesting settings.

    Attributes:
        sources (list[str]): (class attribute) A list of plugins to be executed.
    """

    sources: list[str] = []


def remove_harvest_plugin_from_prov_doc(prov_doc: ld_prov_list, plugin: str) -> None:
    """
    Removes information on the specified harvest plugin from the given provenance document.

    Args:
        prov_doc (ld_prov_list): The provenance document the plugins information is to be removed from.
        plugin (str): The name of the plugin of which the information is to be removed.

    Returns:
        None:
    """
    # get the plugin object from the prov_doc
    plugin = prov_doc.get_hermes_plugin("harvest", plugin)
    # If the plugin isn't contained in the prov_doc, return, otherwise fetch related objects
    if plugin is None:
        return
    related = prov_doc.shallow_search(lambda node: (
        ("prov:wasAssociatedWith" in node and plugin.ref in node["prov:wasAssociatedWith"]) or
        ("prov:wasAttributedTo" in node and plugin.ref in node["prov:wasAttributedTo"])
    ))
    # If no related objects exist, delete only the plugin
    if len(related) == 0:
        del prov_doc[plugin.index]
        return
    # Collect remaining related objects
    ids = [plugin.ref, *(rel.ref for rel in related)]
    used_entities = [rel["prov:used"][0]["@id"] for rel in related if "prov:used" in rel]
    related = prov_doc.shallow_search(lambda node: node["@id"] in used_entities)
    related += prov_doc.shallow_search(lambda node: any(
        (f"prov:{key}" in node and id in node[f"prov:{key}"]) for id in ids for key in [
            "wasAssociatedWith", "wasAttributedTo", "wasGeneratedBy", "used", "wasDerivedFrom", "wasInformedBy"
        ]
    ))
    # delete all collected objects
    del prov_doc[plugin.index]
    for item in related:
        items = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == item["@id"]))
        if len(items) == 1:
            del prov_doc[items[0].index]


class HermesHarvestCommand(HermesCommand):
    """
    Harvest metadata from configured sources.

    Attributes:
        args (Namespace): The arguments of the command.
        command_name (str): (class attribute) The name of the command
        settings_class (type): (class attribute) The settings class for general harvest settings.
    """

    command_name: str = "harvest"
    settings_class: type = HarvestSettings

    def __call__(self: Self, args: argparse.Namespace) -> None:
        """
        Execute the hermes command `self`.

        Args:
            args (Namespace): The arguments of the command.

        Returns:
            None:

        Raises:
            MisconfigurationError: If no plugin is configured to be run.
            HermesPluginRunError: If all plugin runs failed.
        """
        self.args = args
        self.log.info("# Load provenance from old harvest or create new document.")
        # initialize the provenance document for this run
        prov_doc = self.init_provenance_document()
        prov_doc.add_hermes_settings(self)
        prov_doc.add_settings_to_command("harvest", self)
        # get basic hermes object to reference later
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
                plugin_func: HermesHarvestPlugin = self.plugins[plugin_name]()
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
            returned_at_time = datetime.datetime.now()

            self.log.info(f"### Store metadata harvested by {plugin_name} plugin")
            # store harvested data
            begin_store_at_time = datetime.datetime.now()
            harvested_data.write_to_cache(ctx, plugin_name)
            stored_at_time = datetime.datetime.now()
            harvested_any = True

            # remove old provenance data from a potential existent old run of this plugin
            remove_harvest_plugin_from_prov_doc(prov_doc, plugin_name)

            # add the plugins provenance information
            plugin = prov_doc.add_hermes_plugin("harvest", plugin_name, plugin_func, self)
            # add the collected information on the load operations of the plugin to the provenance document
            plugin_operations = plugin_func.operations
            outputs, io_ops = [], []
            for plugin_operation in plugin_operations:
                loaded_source = prov_doc.add_entity(data=plugin_operation[0])
                plugin_operation[1].update(
                    {"prov:wasAssociatedWith": [base_plugin.ref, plugin.ref], "prov:used": loaded_source.ref}
                )
                io_op = prov_doc.add_activity(data=plugin_operation[1])
                plugin_operation[2].update({
                    "prov:wasAttributedTo": plugin.ref,
                    "prov:wasDerivedFrom": loaded_source.ref,
                    "prov:wasGeneratedBy": io_op.ref
                })
                loaded_data = prov_doc.add_entity(data=plugin_operation[2])
                # store references to the added objects
                outputs.append(loaded_data.ref)
                io_ops.append(io_op.ref)

            # add provenance information on the mapping and returned data
            map_activity = prov_doc.add_activity(data={
                "schema:description": "Maps the loaded data to the JSON-LD contexts vocabulary.",
                "prov:wasInformedBy": io_ops,
                "prov:used": outputs,
                "prov:wasAssociatedWith": plugin.ref,
                "prov:endedAtTime": returned_at_time
            })
            data_output = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "the harvested metadata",
                "schema:text": str(harvested_data.compact()),  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": plugin.ref,
                "prov:wasGeneratedBy": map_activity.ref,
                "prov:wasDerivedFrom": outputs,
                "prov:generatedAtTime": returned_at_time
            })

            # add provenance information on the write and stored data
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

        # store provenance information
        with ctx["provenance"] as cache:
            cache["result"] = prov_doc.ld_value

        ctx.finalize_step('harvest')
        if not harvested_any:
            self.log.critical("No harvest plugin ran successfully.")
            raise HermesPluginRunError("No harvest plugin ran successfully.")

    @classmethod
    def init_provenance_document(cls: type[Self]) -> ld_prov_list:
        """
        Loads or creates a provenance document.

        Returns:
            ld_prov_list: The loaded or created provenance document.
        """
        # try loading the document
        ctx = HermesContext()
        ctx.prepare_step("harvest")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                pass
            finally:
                ctx.finalize_step("harvest")
        # initialize a new ld_prov_list because load failed
        prov_doc = ld_prov_list()
        prov_doc.init_hermes_agents()
        return prov_doc
