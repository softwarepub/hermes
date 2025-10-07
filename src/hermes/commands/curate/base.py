# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), 2025 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape

import argparse
import json
import sys

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context import CodeMetaContext
from hermes.model.errors import HermesValidationError
from hermes.model.path import ContextPath


class _CurateSettings(BaseModel):
    """Generic curation settings."""

    #: Parameter by which the plugin is selected. By default, the accept plugin is used.
    method: str = "accept"


class BaseCuratePlugin(HermesPlugin):
    def __init__(self, command, ctx):
        self.command = command
        self.ctx = ctx

    def __call__(self, command: HermesCommand) -> None:
        self.prepare()
        self.validate()
        self.create_report()
        if self.get_decision():
            self.process_decision_positive()
        else:
            self.process_decision_negative()

    def prepare(self):
        pass

    def validate(self):
        pass

    def create_report(self):
        pass

    def get_decision(self) -> bool:
        return False

    def process_decision_positive(self):
        pass

    def process_decision_negative(self):
        raise RuntimeError("Curation declined further processing")


class HermesCurateCommand(HermesCommand):
    """Curate the unified metadata before deposition."""

    command_name = "curate"
    settings_class = _CurateSettings

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        plugin_name = self.settings.method

        ctx = CodeMetaContext()
        process_output = ctx.get_cache("process", ctx.hermes_name)
        if not process_output.exists():
            self.log.error(
                "No processed metadata found. Please run `hermes process` before curation."
            )
            sys.exit(1)

        curate_path = ContextPath("curate")
        with open(process_output) as process_output_fh:
            ctx.update(curate_path, json.load(process_output_fh))

        try:
            plugin_func = self.plugins[plugin_name](self, ctx)

        except KeyError as e:
            self.log.error("Plugin '%s' not found.", plugin_name)
            self.errors.append(e)

        try:
            plugin_func(self)

        except HermesValidationError as e:
            self.log.error("Error while executing %s: %s", plugin_name, e)
            self.errors.append(e)
