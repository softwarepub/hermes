# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from hermes.commands.base import HermesCommand
from hermes.settings import PostprocessSettings


class HermesPostprocessCommand(HermesCommand):
    """ Post-process the published metadata after deposition. """

    command_name = "postprocess"
    settings_class = PostprocessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        pass
