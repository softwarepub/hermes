# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from hermes.commands.base import HermesCommand


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"
    settings_class = None

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        pass
