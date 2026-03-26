# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel

import abc
import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.error import HermesPluginRunError, MisconfigurationError
from hermes.model.context_manager import HermesContext
from hermes.model import SoftwareMetadata
from hermes.model.error import HermesValidationError


class BaseDepositPlugin(HermesPlugin):
    """Base class that implements the generic deposition workflow.

    TODO: describe workflow... needs refactoring to be less stateful!
    """

    def __call__(self, command: HermesCommand) -> None:
        """Initiate the deposition process.

        This calls a list of additional methods on the class, none of which need to be implemented.
        """
        self.command = command
        self.ctx = HermesContext()
        self.ctx.prepare_step("deposit")

        self.ctx.prepare_step("curate")
        try:
            self.metadata = SoftwareMetadata.load_from_cache(self.ctx, "result")
        except Exception as e:
            raise HermesValidationError("The results of the curate step are invalid.") from e
        self.ctx.finalize_step("curate")

        self.prepare()
        deposit = self.map_metadata()
        with self.ctx[command.settings.target] as cache:
            cache["deposit"] = deposit

        if self.is_initial_publication():
            self.create_initial_version()
        else:
            self.create_new_version()

        deposit = self.update_metadata()
        with self.ctx[command.settings.target] as cache:
            cache["result"] = deposit
        self.ctx.finalize_step("deposit")
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

        self.log.info(f"## Load deposit plugin {plugin_name}")
        # load plugin
        try:
            plugin_func = self.plugins[plugin_name]()
        except KeyError:
            self.log.error(f"Plugin {plugin_name} not found.")
            raise MisconfigurationError(f"Deposit plugin {self.settings.plugin} not found.")

        self.log.info(f"## Run deposit plugin {plugin_name}")
        # run plugin
        try:
            plugin_func(self)
        except HermesValidationError as e:
            self.log.error(f"Error while executing {plugin_name}: {e}")
            raise HermesPluginRunError(
                f"Something went wrong while running the deposit plugin {self.settings.plugin}"
            ) from e
