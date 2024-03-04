# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.errors import HermesValidationError
from hermes.model.context import HermesContext, CodeMetaContext


class HermesProcessPlugin(HermesPlugin):
    pass


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"
    settings_class = None

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        # TODO: get harvested data
        # TODO: Merge Datasets


