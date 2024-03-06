# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import os
import shutil
import sys

from pydantic import BaseModel

from hermes.commands.base import HermesCommand
from hermes.model.context import CodeMetaContext


class CurateSettings(BaseModel):
    """Generic deposition settings."""

    pass


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"
    settings_class = CurateSettings

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:

        self.log.info("# Metadata curation")

        ctx = CodeMetaContext()
        process_output = ctx.hermes_dir / 'process' / (ctx.hermes_name + ".json")

        if not process_output.is_file():
            self.log.error(
                "No processed metadata found. Please run `hermes process` before curation."
            )
            sys.exit(1)

        os.makedirs(ctx.hermes_dir / 'curate', exist_ok=True)
        shutil.copy(process_output, ctx.hermes_dir / 'curate' / (ctx.hermes_name + '.json'))
