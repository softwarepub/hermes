# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import click

from hermes.model.context import CodeMetaContext


# TODO: Abstract base class?
class BaseDepositPlugin:
    def __init__(self, click_ctx: click.Context, ctx: CodeMetaContext) -> None:
        self.click_ctx = click_ctx
        self.ctx = ctx

    def __call__(self) -> None:
        # TODO: Decide here which of initial/new/... to run. Contract for decision:
        # Implement method is_new_publication() or similar
        self.prepare()
        self.map_metadata()
        self.create_initial_version()
        self.create_new_version()
        self.update_metadata()
        self.delete_artifacts()
        self.upload_artifacts()
        self.publish()

    def prepare(self) -> None:
        pass

    def map_metadata(self) -> None:
        pass

    def create_initial_version(self) -> None:
        pass

    def create_new_version(self) -> None:
        pass

    def update_metadata(self) -> None:
        pass

    def delete_artifacts(self) -> None:
        pass

    def upload_artifacts(self) -> None:
        pass

    def publish(self) -> None:
        pass
