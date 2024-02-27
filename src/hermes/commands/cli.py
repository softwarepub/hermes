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
    for command in (
            HermesHelpCommand(parser),
            HermesCleanCommand(parser),
            HermesHarvestCommand(parser),
            HermesProcessCommand(parser),
            HermesCurateCommand(parser),
            HermesDepositCommand(parser),
            HermesPostprocessCommand(parser),
    ):
        command_parser = subparsers.add_parser(command.command_name, help=command.__doc__)
        command.init_common_parser(command_parser)
        command.init_command_parser(command_parser)
        command_parser.set_defaults(command=command)

    # Actually parse the commands and execute the selected sub-command.
    args = parser.parse_args()
    args.command(args)
