# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

"""
This module provides the main entry point for the HERMES command line application.
"""
import argparse
import sys

from hermes import logger
from hermes.commands import (
    HermesCurateCommand, HermesCleanCommand, HermesDepositCommand, HermesHarvestCommand, HermesHelpCommand,
    HermesInitCommand, HermesPostprocessCommand, HermesProcessCommand, HermesReportCommand, HermesVersionCommand
)
from hermes.commands.base import HermesCommand
from hermes.error import HermesPluginRunError
from hermes.utils import mask_options_values


def main() -> None:
    """
    HERMES main entry point (i.e., run the CLI).

    This command runs the selected HERMES sub-command.
    """
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="This command runs HERMES workflow steps.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Register all sub-commands to a new sub-parser each.
    subparsers = parser.add_subparsers(dest="subcommand", required=True,
                                       help="Available subcommands")
    setting_types = {}

    for command in (
            HermesCleanCommand(parser),
            HermesCurateCommand(parser),
            HermesDepositCommand(parser),
            HermesHarvestCommand(parser),
            HermesHelpCommand(parser),
            HermesInitCommand(parser),
            HermesPostprocessCommand(parser),
            HermesProcessCommand(parser),
            HermesReportCommand(parser),
            HermesVersionCommand(parser),
    ):
        if command.settings_class is not None:
            setting_types[command.command_name] = command.settings_class

        command_parser = subparsers.add_parser(command.command_name, help=command.__doc__)
        command_parser.set_defaults(command=command)

        command.init_common_parser(command_parser)
        command.init_command_parser(command_parser)

    # Construct the Pydantic Settings root model
    HermesCommand.derive_settings_class(setting_types)

    # Actually parse the command line, configure it and execute the selected sub-command.
    args = parser.parse_args()

    logger.init_logging()
    log = logger.getLogger("hermes.cli")
    log.debug("Running hermes with the following command line arguments: %s", mask_options_values(args))

    try:
        log.debug("Loading settings...")
        args.command.load_settings(args)

        log.debug("Update settings from command line...")
        args.command.patch_settings(args)

        log.info("Run subcommand %s", args.command.command_name)
        args.command(args)
    except HermesPluginRunError:
        log.critical(
            "An error occurred during the execution of the %s command (Find details in './hermes.log')",
            args.command.command_name,
            exc_info=1
        )
        sys.exit(2)
    except Exception:
        log.critical(
            "An error occurred during execution of the %s command (Find details in './hermes.log')",
            args.command.command_name,
            exc_info=1
        )
        sys.exit(1)

    log.info("Finished run of %s command successfully.", args.command.command_name)
    sys.exit(0)
