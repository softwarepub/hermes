# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

import abc
import argparse
import datetime
from typing import Optional

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model import SoftwareMetadata
from hermes.model.error import HermesValidationError
from hermes.model.provenance.ld_prov import ld_prov_list


class BaseDepositPlugin(HermesPlugin):
    """Base class that implements the generic deposition workflow.

    TODO: describe workflow... needs refactoring to be less stateful!
    """

    def __call__(self, command: HermesCommand, prov_doc: ld_prov_list) -> None:
        """Initiate the deposition process.

        This calls a list of additional methods on the class, none of which need to be implemented.
        """
        self.command = command
        target = command.settings.target
        self.ctx = HermesContext()
        self.ctx.prepare_step("deposit")

        self.ctx.prepare_step("curate")
        try:
            start_of_load = datetime.datetime.now()
            self.metadata = SoftwareMetadata.load_from_cache(self.ctx, "result")
            end_of_load = datetime.datetime.now()
        except Exception as e:
            raise HermesValidationError("The results of the curate step are invalid.") from e
        self.ctx.finalize_step("curate")

        if prov_doc is not None:
            plugin = prov_doc.add_hermes_plugin("deposit", target, self, command)
            deposit_command = prov_doc.get_hermes_command("deposit")
            curate_command = prov_doc.get_hermes_command("curate")
            deposit_base_plugin = prov_doc.get_hermes_base_plugin("deposit")
            hermes_cache = prov_doc.get_hermes_cache()
            store_action_curate = prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and
                node["prov:wasAssociatedWith"] == [curate_command.ref, hermes_cache.ref] and
                "prov:used" in node and
                len(node["prov:used"]) == 1
            ))[0]
            results_curate = [item.ref for item in prov_doc.shallow_search(lambda node: (
                "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action_curate.ref]
            ))]
            load_action = prov_doc.add_activity(data={
                "schema:description": "Loads the results of the curate step.",
                "prov:used": results_curate,
                "prov:wasAssociatedWith": [hermes_cache.ref, deposit_command.ref, deposit_base_plugin.ref],
                "prov:startedAtTime": start_of_load,
                "prov:endedAtTime": end_of_load
            })
            loaded_data = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "data loaded from curate step",
                "schema:text": str(self.metadata.compact()),  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:wasGeneratedBy": load_action.ref,
                "prov:wasDerivedFrom": results_curate,
                "prov:generatedAtTime": end_of_load
            })

        self.prepare()
        start_of_map = datetime.datetime.now()
        deposit = self.map_metadata()
        end_of_map = datetime.datetime.now()
        with self.ctx[target] as cache:
            cache["deposit"] = deposit
        end_of_store = datetime.datetime.now()

        if prov_doc is not None:
            map_action = prov_doc.add_activity(data={
                "schema:description": "Maps the metadata to the format required by the deposition target.",
                "prov:used": loaded_data.ref,
                "prov:wasAssociatedWith": plugin.ref,
                "prov:startedAtTime": start_of_map,
                "prov:endedAtTime": end_of_map
            })
            mapped_data = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The metadata mapped to the format required by the deposition target.",
                "schema:text": str(deposit),  # TODO: maybe "prov:value" instead?
                "prov:wasAttributedTo": plugin.ref,
                "prov:wasGeneratedBy": map_action.ref,
                "prov:wasDerivedFrom": loaded_data.ref,
                "prov:generatedAtTime": end_of_load
            })
            store_mapped_data = prov_doc.add_activity(data={
                "schema:description": "Stores the mapped metadata.",
                "prov:used": mapped_data.ref,
                "prov:wasAssociatedWith": [hermes_cache.ref, deposit_command.ref, deposit_base_plugin.ref],
                "prov:startedAtTime": end_of_map,
                "prov:endedAtTime": end_of_store
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The stored version of the mapped metadata.",
                "schema:text": str(deposit),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (self.ctx.cache_dir / "deposit" / target / "deposit.json").absolute().as_uri(),
                "prov:wasGeneratedBy": store_mapped_data.ref,
                "prov:wasDerivedFrom": mapped_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": end_of_store
            })

        if self.is_initial_publication():
            self.create_initial_version()
        else:
            self.create_new_version()

        updated_deposit = self.update_metadata()
        end_of_update_map = datetime.datetime.now()
        with self.ctx[target] as cache:
            cache["result"] = updated_deposit
        end_of_second_store = datetime.datetime.now()
        self.ctx.finalize_step("deposit")

        if prov_doc is not None:
            updated_mapped_data = prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The updated mapped metadata.",
                "schema:text": str(updated_deposit),  # TODO: maybe "prov:value" instead?
                "prov:wasInfluencedBy": plugin.ref,
                "prov:wasDerivedFrom": mapped_data.ref,
                "prov:generatedAtTime": end_of_update_map
            })
            store_updated_mapped_data = prov_doc.add_activity(data={
                "schema:description": "Stores the mapped metadata.",
                "prov:used": updated_mapped_data.ref,
                "prov:wasAssociatedWith": [hermes_cache.ref, deposit_command.ref, deposit_base_plugin.ref],
                "prov:startedAtTime": end_of_update_map,
                "prov:endedAtTime": end_of_second_store
            })
            prov_doc.add_entity(data={
                "@type": "schema:CreativeWork",
                "schema:description": "The stored version of the updated mapped metadata.",
                "schema:text": str(updated_deposit),  # TODO: maybe "prov:value" instead?
                "schema:encodingFormat": "application/json",
                "schema:url": (self.ctx.cache_dir / "deposit" / target / "result.json").absolute().as_uri(),
                "prov:wasGeneratedBy": store_updated_mapped_data.ref,
                "prov:wasDerivedFrom": updated_mapped_data.ref,
                "prov:wasAttributedTo": hermes_cache.ref,
                "prov:generatedAtTime": end_of_second_store
            })

        self.delete_artifacts()
        self.upload_artifacts()
        self.publish()

    def prepare(self) -> None:
        """Prepare the deposition.

        This method may be implemented to check whether config and context match some initial conditions.

        If no exceptions are raised, execution continues.
        """
        pass

    @abc.abstractmethod
    def map_metadata(self) -> dict:
        """Map the given metadata to the target schema of the deposition platform and return it.

        When mapping metadata, make sure to add traces to the HERMES software, e.g. via
        DataCite's ``relatedIdentifier`` using the ``isCompiledBy`` relation. Ideally, the value
        of the relation target should be of the respective type for DOIs in your metadata
        schema, with the value itself being the DOI for the version of the HERMES software
        you are using.
        """
        pass

    def is_initial_publication(self) -> bool:
        """Decide whether to do an initial publication or publish a new version.

        Returning ``True`` indicates that publication of an initial version will be executed, resulting in a call of
        :meth:`create_initial_version`. ``False`` indicates a new version of an existing publication, leading to a call
        of :meth:`create_new_version`.

        By default, this returns ``True``.
        """
        return True

    def create_initial_version(self) -> None:
        """Create an initial version of the publication on the target platform."""
        pass

    def create_new_version(self) -> None:
        """Create a new version of an existing publication on the target platform."""
        pass

    @abc.abstractmethod
    def update_metadata(self) -> dict:
        """Update the metadata of the newly created version and return it even if it hasn't changed."""
        pass

    def delete_artifacts(self) -> None:
        """Delete any superfluous artifacts taken from the previous version of the publication."""
        pass

    def upload_artifacts(self) -> None:
        """Upload new artifacts to the target platform."""
        pass

    @abc.abstractmethod
    def publish(self) -> None:
        """Publish the newly created deposit on the target platform."""
        pass


class DepositSettings(BaseModel):
    """Generic deposition settings."""

    target: str = ""


class HermesDepositCommand(HermesCommand):
    """ Deposit the curated metadata to repositories. """

    command_name = "deposit"
    settings_class = DepositSettings

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('--file', '-f', nargs=1, action='append',
                                    help="File that should be part of the deposition.")
        command_parser.add_argument('--initial', action='store_true', default=False,
                                    help="Allow initial deposition (i.e., minting a new PID).")

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("# Metadata deposition")
        self.args = args
        plugin_name = self.settings.target
        prov_doc = self.load_prov_doc()
        if prov_doc is not None:
            prov_doc.add_hermes_settings(self)
            prov_doc.add_settings_to_command("deposit", self)

        self.log.info(f"## Load deposit plugin {plugin_name}")
        # load plugin
        try:
            plugin_func = self.plugins[plugin_name]()
        except KeyError:
            self.log.critical(f"## Deposit plugin {plugin_name} not found.")
            raise MisconfigurationError(f"Deposit plugin {self.settings.plugin} not found.")

        self.log.info(f"## Run deposit plugin {plugin_name}")
        # run plugin
        try:
            plugin_func(self, prov_doc)
        except HermesValidationError as e:
            self.log.critical(f"## Error while executing {plugin_name} plugin.", exc_info=1)
            raise HermesPluginRunError(
                f"Something went wrong while running the deposit plugin {self.settings.plugin}"
            ) from e

        if prov_doc is None:
            return

        ctx = HermesContext()
        ctx.prepare_step("deposit")
        with ctx["provenance"] as cache:
            cache["result"] = prov_doc.ld_value
        ctx.finalize_step("deposit")

    def load_prov_doc(self) -> Optional[ld_prov_list]:
        ctx = HermesContext()
        ctx.prepare_step("curate")
        with ctx["provenance"] as cache:
            try:
                return ld_prov_list.load_ld_prov_list(cache["result"])
            except Exception:
                self.log.warning(
                    "The provenance data from the curate step could not be loaded. "
                    "Deposition will proceed without collecting provenance data.",
                    exc_info=1
                )
            finally:
                ctx.finalize_step("curate")
