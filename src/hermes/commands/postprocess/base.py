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

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError
from hermes.model.context_manager import HermesContext
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesPostprocessPlugin(HermesPlugin):
    """ Base plugin for postprocess plugins. """

    def __init__(self):
        self.cache_operations: list[tuple[str, dict, dict]] = []
        self.load_operations: list[tuple[dict, dict, dict]] = []
        self.write_operations: list[tuple[dict, dict, dict]] = []
        super().__init__()

    def __call__(self, command: HermesCommand) -> None:
        pass

    def get_deposit_result(self, target: str) -> dict:
        source_metadata = target[:]
        load_operation = {"schema:description": f"loads the result of deposit plugin {target}"}
        ctx = HermesContext()
        ctx.prepare_step("deposit")
        load_operation["prov:startedAtTime"] = datetime.datetime.now()
        with ctx[target] as cache:
            res = cache["result"]
        load_operation["prov:endedAtTime"] = datetime.datetime.now()
        ctx.finalize_step("deposit")
        loaded_data = {"schema:description": "the loaded data", "schema:text": str(res)}
        self.cache_operations.append((source_metadata, load_operation, loaded_data))
        return res

    def load(self, func: Callable, source: Any, *args, **kwargs) -> Any:
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
        result = func(source, *args, **kwargs)
        load_operation["prov:endedAtTime"] = datetime.datetime.now()
        loaded_metadata = {"schema:description": "the loaded data", "schema:text": str(result)}
        self.load_operations.append((source_metadata, load_operation, loaded_metadata))
        return result

    def write(self, func: Callable, data: Any, destination: Any, *args, **kwargs) -> Any:
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
        result = func(data, destination, *args, **kwargs)
        write_operation["prov:endedAtTime"] = datetime.datetime.now()
        written_metadata = {"schema:description": "the written data", "schema:text": str(data)}
        self.write_operations.append((written_metadata, write_operation, destination_metadata))
        return result


class PostprocessSettings(BaseModel):
    """Generic post-processing settings."""

    run: list = []


class HermesPostprocessCommand(HermesCommand):
    """Post-process the published metadata after deposition."""

    command_name = "postprocess"
    settings_class = PostprocessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Postprocessing")
        self.args = args
        plugin_names = self.settings.run
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            prov_doc.add_hermes_settings(self)
            prov_doc.add_settings_to_command("postprocess", self)
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
                plugin_func = self.plugins[plugin_name]()
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

            plugin = prov_doc.add_hermes_plugin("postprocess", plugin_name, plugin_func, self)
            cache_loads = plugin_func.cache_operations
            loads = plugin_func.load_operations
            writes = plugin_func.write_operations
            load_actions, loaded_datas = [], []
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
            for write in writes:
                data = prov_doc.add_entity(data=write[0])
                data.update({"prov:wasDerivedFrom": loaded_datas, "prov:wasInfluencedBy": plugin.ref})
                write_action = prov_doc.add_activity(data=write[1])
                write_action.update({
                    "prov:used": data.ref,
                    "prov:wasAssociatedWith": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })
                written_data = prov_doc.add_entity(data=write[2])
                written_data.update({
                    "prov:wasGeneratedBy": write_action.ref,
                    "prov:wasDerivedFrom": data.ref,
                    "prov:wasAttributedTo": [plugin.ref, postprocess_base_plugin.ref, postprocess_command.ref]
                })

        if prov_doc is not None:
            ctx = HermesContext()
            ctx.prepare_step("postprocess")
            with ctx["provenance"] as cache:
                cache["result"] = prov_doc.ld_value
            ctx.finalize_step("postprocess")

        if not ran_any:
            self.log.critical("## No postprocess plugin ran successfully.")
            raise HermesPluginRunError("No postprocess plugin ran successfully.")

    def load_prov_doc(self) -> Optional[ld_prov_list]:
        ctx = HermesContext()
        ctx.prepare_step("deposit")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except Exception:
                self.log.warning(
                    "The provenance data from the deposit step could not be loaded. "
                    "Postprocessing will proceed without collecting provenance data.",
                    exc_info=1
                )
            finally:
                ctx.finalize_step("deposit")
