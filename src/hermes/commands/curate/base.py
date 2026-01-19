# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand
from hermes.model import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesValidationError


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

        ctx = HermesContext()
        ctx.prepare_step("curate")

        ctx.prepare_step("process")
        with ctx["result"] as process_ctx:
            expanded_data = process_ctx["expanded"]
            context_data = process_ctx["context"]
        ctx.finalize_step("process")

        try:
            data = SoftwareMetadata(expanded_data[0], context_data["@context"][1])
        except Exception as e:
            raise HermesValidationError("The results of the process step are invalid.") from e

        with ctx["result"] as curate_ctx:
            curate_ctx["expanded"] = data.ld_value
            curate_ctx["context"] = {"@context": data.full_context}

        ctx.finalize_step("curate")
