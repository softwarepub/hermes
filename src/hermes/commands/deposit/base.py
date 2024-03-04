# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel

import abc
import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin


class BaseDepositPlugin(HermesPlugin):
    """Base class that implements the generic deposition workflow.

    TODO: describe workflow... needs refactoring to be less stateful!
    """

    def __init__(self, ctx):
        self.ctx = ctx

    def __call__(self, command: HermesCommand) -> None:
        """Initiate the deposition process.

        This calls a list of additional methods on the class, none of which need to be implemented.
        """
        self.prepare()
        self.map_metadata()

        if self.is_initial_publication():
            self.create_initial_version()
        else:
            self.create_new_version()

        self.update_metadata()
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
    def map_metadata(self) -> None:
        """Map the given metadata to the target schema of the deposition platform."""
        pass

    def is_initial_publication(self) -> bool:
        """Decide whether to do an initial publication or publish a new version.

        Returning ``True`` indicates that publication of an initial version will be executed, resulting in a call of
        :meth:`create_initial_version`. ``False`` indicates a new version of an existing publication, leading to a call
        of :meth:`create_new_version`.

        By default, this returns ``True``.
        """
        return True

    @abc.abstractmethod
    def create_initial_version(self) -> None:
        """Create an initial version of the publication on the target platform."""
        pass

    @abc.abstractmethod
    def create_new_version(self) -> None:
        """Create a new version of an existing publication on the target platform."""
        pass

    @abc.abstractmethod
    def update_metadata(self) -> None:
        """Update the metadata of the newly created version."""
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

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        plugin_name = self.settings.target
        '''try:
            plugin_func = self.plugins[plugin_name](ctx)
            deposited_data = plugin_func(self)


        except KeyError:
            self.log.error("Plugin '%s' not found.", plugin_name)

        except HermesValidationError as e:
            self.log.error("Error while executing %s: %s", plugin_name, e)'''
