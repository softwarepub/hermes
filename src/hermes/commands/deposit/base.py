# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import click

from hermes.model.context import CodeMetaContext


class BaseDepositPlugin:
    def __init__(self, click_ctx: click.Context, ctx: CodeMetaContext) -> None:
        self.click_ctx = click_ctx
        self.ctx = ctx

    def __call__(self) -> None:
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

    def create_initial_version(self) -> None:
        """Create an initial version of the publication on the target platform."""
        pass

    def create_new_version(self) -> None:
        """Create a new version of an existing publication on the target platform."""
        pass

    def update_metadata(self) -> None:
        """Update the metadata of the newly created version."""
        pass

    def delete_artifacts(self) -> None:
        """Delete any superfluous artifacts taken from the previous version of the publication."""
        pass

    def upload_artifacts(self) -> None:
        """Upload new artifacts to the target platform."""
        pass

    def publish(self) -> None:
        """Publish the newly created deposit on the target platform."""
        pass
