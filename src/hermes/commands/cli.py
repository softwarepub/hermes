# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

"""
This module provides the main entry point for the HERMES command line application.
"""
import argparse

from hermes.commands import HermesHelpCommand, HermesCleanCommand, HermesHarvestCommand, HermesProcessCommand, \
                            HermesCurateCommand, HermesDepositCommand, HermesPostprocessCommand
from hermes.commands.base import HermesCommand


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
            HermesHelpCommand(parser),
            HermesCleanCommand(parser),
            HermesHarvestCommand(parser),
            HermesProcessCommand(parser),
            HermesCurateCommand(parser),
            HermesDepositCommand(parser),
            HermesPostprocessCommand(parser),
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

    args.command.load_settings(args)
    args.command.patch_settings(args)
    args.command(args)
