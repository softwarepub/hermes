# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import shutil

from pydantic import BaseModel

from hermes.commands.base import HermesCommand


class HermesCleanSettings(BaseModel):
    """Configuration of the ``clean`` command."""
    pass


class HermesCleanCommand(HermesCommand):
    """ Clean up caches from previous HERMES runs. """

    command_name = "clean"
    settings_class = HermesCleanSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.log.info("Removing HERMES caches...")

        # Naive implementation for now... check errors, validate directory, don't construct the path ourselves, etc.
        shutil.rmtree(args.path / '.hermes')
