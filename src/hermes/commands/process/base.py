# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from hermes.commands.base import HermesCommand, HermesPlugin


class HermesProcessPlugin(HermesPlugin):
    pass


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"

    def __call__(self, args: argparse.Namespace) -> None:
        pass
