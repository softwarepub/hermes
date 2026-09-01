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
from hermes.error import HermesPluginRunError
from hermes.model.hermes_cache import HermesCacheManager
from hermes.model.provenance.ld_prov import ld_prov_list
from hermes.model.types import ld_dict


class HermesPostprocessPlugin(HermesPlugin):
    """
    Base plugin for postprocess plugins.

    Attributes:
        cache_operations (list[tuple[str, dict[str, str], dict[str, str]]]): The information recorded on the
            cache load operations executed by the plugin.
        load_operations (list[tuple[dict[str, str], dict[str, str], dict[str, str]]]): The information recorded on the
            load operations executed by the plugin.
        write_operations (list[tuple[dict[str, str], dict[str, str], dict[str, str]]]): The information recorded on the
            write operations executed by the plugin.
    """

    def __init__(self: Self) -> None:
        """
        Create a new instance of a HermesPostprocessPlugin.

        Returns:
            None:
        """
        self.cache_operations: list[tuple[str, dict[str, str], dict[str, str]]] = []
        self.load_operations: list[tuple[dict[str, str], dict[str, str], dict[str, str]]] = []
        self.write_operations: list[tuple[dict[str, str], dict[str, str], dict[str, str]]] = []
        super().__init__()

    def __call__(self: Self, command: "HermesPostprocessCommand") -> None:
        """
        Execute the hermes postprocess plugin `self`.

        Args:
            command (HermesPostprocessCommand): The command being executed.

        Returns:
            None:
        """
        pass

    def get_deposit_result(self: Self, target: str) -> dict:
        """
        Load the result of some deposit plugin from the cache so that the calls provenance information is recorded.

        Args:
            target (str): The name of the deposit plugin.

        Returns:
            dict: The result of the cache load operation.
        """
        # collect basic metadata
        source_metadata = target[:]
        load_operation = {"schema:description": f"loads the result of deposit plugin {target}"}
        ctx = HermesCacheManager()
        ctx.prepare_step("deposit")
        load_operation["prov:startedAtTime"] = datetime.datetime.now()
        # execute the load operation
        with ctx[target] as cache:
            res = cache["result"]
        # complete metadata collection
        load_operation["prov:endedAtTime"] = datetime.datetime.now()
        ctx.finalize_step("deposit")
        loaded_data = {"schema:description": "the loaded data", "schema:text": str(res)}
        # store metadata
        self.cache_operations.append((source_metadata, load_operation, loaded_data))
        # return result of the load operation
        return res

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
        load_operation = {
            "schema:description": "Load operation called with ("
            f"{source_metadata['schema:url'] if 'schema:url' in source_metadata else str(source)}"
            f"{', ' + str(args) if args else ''}{', ' + str(kwargs) if kwargs else ''}).",
            "schema:name": f"{func.__module__}.{func.__qualname__}"
        }
        load_operation["prov:startedAtTime"] = datetime.datetime.now()
        # execute the load operation
        result = func(source, *args, **kwargs)
        # complete metadata collection
        load_operation["prov:endedAtTime"] = datetime.datetime.now()
        loaded_metadata = {"schema:description": "the loaded data", "schema:text": str(result)}
        # store metadata
        self.load_operations.append((source_metadata, load_operation, loaded_metadata))
        # return result of the load operation
        return result

    def write(
        self: Self, func: Callable, data: Any, destination: Any, *args: Optional[Any], **kwargs: Optional[Any]
    ) -> Any:
        """
        Write some data from some source using some function so that the calls provenance information is recorded.

        `func(source, *args, **kwargs)` will be executed.

        Args:
            func (Callable): The function used for writing the requested source.
            data (Any): The data that is to be written.
            destination (Any): The source the data is to be written to.
            args (Any | None): Additional positional arguments for the write.
            kwargs (Any | None): Additional keyword arguments for the write.

        Returns:
            Any: The result of the write operation.
        """
        # collect basic metadata
        destination_metadata = {"schema:description": "metadata destination"}
        if isinstance(destination, IOBase):
            destination_metadata["schema:url"] = Path(destination.name).absolute().as_uri()
        elif isinstance(destination, Path):
            destination_metadata["schema:url"] = destination.absolute().as_uri()
        elif isinstance(destination, str):
            try:
                destination_metadata["schema:url"] = Path(destination).absolute().as_uri()
            except Exception:
                destination_metadata["schema:url"] = destination
        write_operation = {
            "schema:description": f"Write operation called with ({str(data)},"
            f"{destination_metadata['schema:url'] if 'schema:url' in destination_metadata else str(destination)}"
            f"{', ' + str(args) if args else ''}{', ' + str(kwargs) if kwargs else ''}).",
            "schema:name": f"{func.__module__}.{func.__qualname__}"
        }
        write_operation["prov:startedAtTime"] = datetime.datetime.now()
        # execute the write operation
        result = func(data, destination, *args, **kwargs)
        # complete metadata collection
        write_operation["prov:endedAtTime"] = datetime.datetime.now()
        written_metadata = {"schema:description": "the written data", "schema:text": str(data)}
        # store metadata
        self.write_operations.append((written_metadata, write_operation, destination_metadata))
        # return result of the write operation
        return result


class PostprocessSettings(BaseModel):
    """
    Generic post-processing settings.

    Attributes:
        run (list[str]): A list of plugins to be executed.
    """

    run: list[str] = []


class HermesPostprocessCommand(HermesCommand):
    """
    Post-process the published metadata after deposition.

    Attributes:
        args (Namespace): The namespace that was returned by the command line parser when reading the arguments.
        command_name (str): (class attribute) The name of the command.
        settings_class (type): (class attribute) The settings class for general deposit settings.
    """

    command_name: str = "postprocess"
    settings_class: type = PostprocessSettings

    def __call__(self: Self, args: argparse.Namespace) -> None:
        """
        Execute the hermes command `self`.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:

        Raises:
            HermesPluginRunError: If something went wrong with all plugin runs.
        """
        self.log.info("# Postprocessing")
        self.args = args
        plugin_names = self.settings.run
        # try loading and adding general information to the provenance document
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            prov_doc.add_hermes_settings(self)
            prov_doc.add_settings_to_command("postprocess", self)
            # get basic hermes objects to reference later
            hermes_cache = prov_doc.get_hermes_cache()
            postprocess_command = prov_doc.get_hermes_command("postprocess")
            postprocess_base_plugin = prov_doc.get_hermes_base_plugin("postprocess")

        if not plugin_names:
            self.log.warning("# No plugin was configured to be run yet the postprocess command was executed.")
            return

        self.log.info("## Load and run the plugins")
        ran_any = False
        for plugin_name in plugin_names:
            self.log.info(f"### Load {plugin_name} plugin")
            # load plugin
            try:
                plugin_func: HermesPostprocessPlugin = self.plugins[plugin_name]()
            except KeyError:
                self.log.error(f"### Plugin {plugin_name} not found.")
                continue

            self.log.info(f"### Run {plugin_name} plugin")
            # run plugin
            try:
                plugin_func(self)
            except Exception:
                self.log.exception(f"### Unknown error while executing the {plugin_name} plugin.")
                continue

            ran_any = True

            if prov_doc is None:
                continue

            # add information on the postprocess plugin
            plugin = prov_doc.add_hermes_plugin("postprocess", plugin_name, plugin_func, self)
            # add the collected information on the io operations of the plugin to the provenance document
            cache_loads = plugin_func.cache_operations
            loads = plugin_func.load_operations
            writes = plugin_func.write_operations
            load_actions: list[ld_dict] = []
            loaded_datas: list[ld_dict] = []
            # add cache load operations to the provenance document
            for cache_load in cache_loads:
                deposit_plugin = prov_doc.get_hermes_plugin("postprocess", cache_load[0])
                updated_metadata = prov_doc.shallow_search(lambda node: (
                    "prov:wasInfluencedBy" in node and node["prov:wasInfluencedBy"] == [deposit_plugin.ref]
                ))[0]
                updated_metadata = prov_doc.shallow_search(lambda node: (
                    "prov:wasDerivedFrom" in node and node["prov:wasDerivedFrom"] == [updated_metadata.ref]
                ))[0]
                load_actions.append(prov_doc.add_activity(data=cache_load[1]))
                load_actions[-1].update({
                    "prov:used": updated_metadata.ref,
                    "prov:wasAssociatedWith": [
                        plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref, hermes_cache.ref
                    ]
                })
                loaded_datas.append(prov_doc.add_entity(data=cache_load[2]))
                loaded_datas[-1].update({
                    "prov:wasGeneratedBy": load_actions[-1].ref,
                    "prov:wasDerivedFrom": updated_metadata.ref,
                    "prov:wasAttributedTo": hermes_cache.ref
                })
            # add load operations to the provenance document
            for load in loads:
                source = prov_doc.add_entity(data=load[0])
                load_actions.append(prov_doc.add_activity(data=load[1]))
                load_actions[-1].update({
                    "prov:used": source.ref,
                    "prov:wasAssociatedWith": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })
                loaded_datas.append(prov_doc.add_entity(data=load[2]))
                loaded_datas[-1].update({
                    "prov:wasGeneratedBy": load_actions[-1].ref,
                    "prov:wasDerivedFrom": source.ref,
                    "prov:wasAttributedTo": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })
            load_actions = [load_action.ref for load_action in load_actions]
            loaded_datas = [loaded_data.ref for loaded_data in loaded_datas]
            # add write operations to the provenance document
            for write in writes:
                data = prov_doc.add_entity(data=write[0])
                data.update({"prov:wasDerivedFrom": loaded_datas, "prov:wasInfluencedBy": plugin.ref})
                write_action = prov_doc.add_activity(data=write[1])
                write_action.update({
                    "prov:used": data.ref,
                    "prov:wasAssociatedWith": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })
                prov_doc.add_entity(data=write[2]).update({
                    "prov:wasGeneratedBy": write_action.ref,
                    "prov:wasDerivedFrom": data.ref,
                    "prov:wasAttributedTo": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })

        if prov_doc is not None:
            # store provenance data
            ctx = HermesCacheManager()
            ctx.prepare_step("postprocess")
            with ctx["provenance"] as cache:
                cache["result"] = prov_doc.ld_value
            ctx.finalize_step("postprocess")

        # error out if no plugin ran successfully
        if not ran_any:
            self.log.critical("## No postprocess plugin ran successfully.")
            raise HermesPluginRunError("No postprocess plugin ran successfully.")

    def load_prov_doc(self: Self) -> Optional[ld_prov_list]:
        """
        Loads the provenance document of the postprocess step.

        Returns:
            ld_prov_list | None: The loaded provenance document or None if the load failed.
        """
        # set up HermesContext
        ctx = HermesCacheManager()
        ctx.prepare_step("deposit")
        with ctx["provenance"] as cache:
            # try load
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except Exception:
                # log the warning and return None
                self.log.warning(
                    "The provenance data from the deposit step could not be loaded. "
                    "Postprocessing will proceed without collecting provenance data.",
                    exc_info=1
                )
            finally:
                ctx.finalize_step("deposit")
