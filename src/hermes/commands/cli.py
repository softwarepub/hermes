# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

"""
This module provides the main entry point for the HERMES command line application.
"""
import argparse
import pathlib
from importlib import metadata

from pydantic import BaseModel

from hermes.settings import DepositSettings, HarvestSettings, PostprocessSettings


class HermesCommand:
    """ Base class for a HERMES workflow command.

    :cvar NAME: The name of the sub-command that is defined here.
    """

    NAME: str = None
    settings_class: type = BaseModel

    def __init__(self, parser: argparse.ArgumentParser):
        """ Initialize a new instance of any HERMES command.

        :param parser: The command line parser used for reading command line arguments.
        """
        self.parser = parser
        self.plugins = self.init_plugins()

    def init_plugins(self):
        # Collect all entry points for this group (i.e., all valid plug-ins for the step)
        entry_point_group = f"hermes.{self.NAME}"
        group_plugins = [
            (entry_point.name, entry_point.load())
            for entry_point in metadata.entry_points(group=entry_point_group)
        ]

        # Collect the plug-in specific configurations
        plugin_settings = {
            plugin_name: getattr(plugin_class, 'settings_class', None)
            for plugin_name, plugin_class in group_plugins
        }

        # Derive a new settings model class that contains all the plug-in extensions
        self.settings_class = type(f'{self.__class__.__name__}Settings', (self.settings_class, ), {
            '__annotations__': plugin_settings,
            **{
                plugin_name: plugin_settings()
                for plugin_name, plugin_settings in plugin_settings.items()
                if plugin_settings is not None
            }
        })

        return group_plugins

    def init_common_parser(self, parser: argparse.ArgumentParser) -> None:
        """ Initialize the common command line arguments available for all HERMES sub-commands.

        :param parser: The base command line parser used as entry point when reading command line arguments.
        """

        parser.add_argument("--path", default=pathlib.Path(), type=pathlib.Path,
                            help="Working path")
        parser.add_argument("--config", default=pathlib.Path("hermes.toml"), type=pathlib.Path,
                            help="Configuration file in TOML format")

        plugin_args = parser.add_argument_group("Extra plug-in options")
        plugin_args.add_argument("-O", nargs=2, action='append', metavar=("NAME", "VALUE"),
                                 help="Configuration values to override hermes.toml options. "
                                      "NAME is the dotted name / path to the option in the TOML file."
                                      "VALUE the actual value.")

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        """ Initialize the command line arguments available for this specific HERMES sub-commands.

        You should override this method to add your custom arguments to the command line parser of
        the respective sub-command.

        :param command_parser: The command line sub-parser responsible for the HERMES sub-command.
        """

        pass

    def __call__(self, args: argparse.Namespace):
        """ Execute the HERMES sub-command.

        :param args: The namespace that was returned by the command line parser when reading the arguments.
        """

        pass


class HermesHelpCommand(HermesCommand):
    """ Show help page and exit. """

    NAME = "help"

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('subcommand', nargs='?', metavar="COMMAND",
                                    help="The HERMES sub-command to get help for.")

    def __call__(self, args: argparse.Namespace) -> None:
        if args.subcommand:
            # When a sub-command is given, show its help page (i.e., by "running" the command with "-h" flag).
            self.parser.parse_args([args.subcommand, '-h'])
        else:
            # Otherwise, simply show the general help and exit (cleanly).
            self.parser.print_help()
            self.parser.exit()


class HermesCleanCommand(HermesCommand):
    """ Clean up caches from previous HERMES runs. """

    NAME = "clean"


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    NAME = "harvest"
    settings_class = HarvestSettings


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    NAME = "process"


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    NAME = "curate"


class HermesDepositCommand(HermesCommand):
    """ Deposit the curated metadata to repositories. """

    NAME = "deposit"
    settings_class = DepositSettings


class HermesPostprocessCommand(HermesCommand):
    """ Post-process the published metadata after deposition. """

    NAME = "postprocess"
    settings_class = PostprocessSettings


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
        command_parser = subparsers.add_parser(command.NAME, help=command.__doc__)
        command.init_common_parser(command_parser)
        command.init_command_parser(command_parser)
        command_parser.set_defaults(command=command)

    # Actually parse the commands and execute the selected sub-command.
    args = parser.parse_args()
    args.command(args)
