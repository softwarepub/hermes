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
    """Base class for curation plugins."""

    def __init__(self, command, ctx):
        self.command = command
        self.ctx = ctx

    def __call__(self, command: HermesCommand) -> None:
        """Entry point of the callable.

        This method runs the main logic of the plugin. It calls the other methods of the
        object in the correct order. Depending on the result of
        ``is_publication_approved`` the corresponding ``process_decision_*()`` method is
        called, based on the curation decision.
        """
        self.prepare()
        self.validate()
        self.create_report()
        if self.is_publication_approved():
            self.process_decision_positive()
        else:
            self.process_decision_negative()

    def prepare(self):
        """Prepare the plugin.

        This method may be used to perform preparatory tasks such as configuration
        checks, token permission checks, loading of resources, etc.
        """
        pass

    def validate(self):
        """Validate the metadata.

        This method performs the validation of the metadata from the data model.
        """
        pass

    def create_report(self):
        """Create a curation report.

        This method is responsible for creating any number of reports about the curation
        process. These reports may be machine-readable, human-readable, or both.
        """
        pass

    def is_publication_approved(self) -> bool:
        """Return the publication decision made through the curation process.

        If publication is allowed, this method must return ``True``. By default,
        ``False`` is returned.
        """
        return False

    def process_decision_positive(self):
        """Process a positive curation decision.

        This method is called if a positive publication decision was made in the
        curation process.
        """
        pass

    def process_decision_negative(self):
        """Process a negative curation decision.

        This method is called if a negative publication decision was made in the
        curation process. By default, a ``RuntimeError`` is raised, halting the
        execution.
        """
        raise RuntimeError("Curation declined further processing")


class HermesCurateCommand(HermesCommand):
    """Curate the processed metadata before deposition."""

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
