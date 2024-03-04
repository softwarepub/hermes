# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import abc
import argparse
import logging
import pathlib
from importlib import metadata
from typing import Dict, Optional, Type

import toml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class HermesSettings(BaseSettings):
    """Root class for HERMES configuration model."""

    model_config = SettingsConfigDict(env_file_encoding='utf-8')

    logging: Dict = {}


class HermesCommand(abc.ABC):
    """Base class for a HERMES workflow command.

    :cvar NAME: The name of the sub-command that is defined here.
    """

    command_name: str = ""
    settings_class: Type = HermesSettings

    def __init__(self, parser: argparse.ArgumentParser):
        """Initialize a new instance of any HERMES command.

        :param parser: The command line parser used for reading command line arguments.
        """
        self.parser = parser
        self.plugins = self.init_plugins()
        self.settings = None

        self.log = logging.getLogger(f"hermes.{self.command_name}")

    def init_plugins(self):
        """Collect and initialize the plugins available for the HERMES command."""

        # Collect all entry points for this group (i.e., all valid plug-ins for the step)
        entry_point_group = f"hermes.{self.command_name}"
        group_plugins = {
            entry_point.name: entry_point.load()
            for entry_point in metadata.entry_points(group=entry_point_group)
        }

        # Collect the plug-in specific configurations
        self.derive_settings_class({
            plugin_name: plugin_class.settings_class
            for plugin_name, plugin_class in group_plugins.items()
            if hasattr(plugin_class, "settings_class") and plugin_class.settings_class is not None
        })

        return group_plugins

    @classmethod
    def derive_settings_class(cls, setting_types: Dict[str, Type]) -> None:
        """Build a new Pydantic data model class for configuration.

        This will create a new class that includes all settings from the plugins available.
        """

        if cls.settings_class is not None:
            # Derive a new settings model class that contains all the plug-in extensions
            cls.settings_class = type(
                f"{cls.__name__}Settings",
                (cls.settings_class, ),
                {
                    **{
                        plugin_name: plugin_settings()
                        for plugin_name, plugin_settings in setting_types.items()
                        if plugin_settings is not None
                    },
                    "__annotations__": setting_types,
                },
            )
        elif setting_types:
            raise ValueError(f"Command {cls.command_name} has no settings, hence plugin must not have settings, too.")

    def init_common_parser(self, parser: argparse.ArgumentParser) -> None:
        """Initialize the common command line arguments available for all HERMES sub-commands.

        :param parser: The base command line parser used as entry point when reading command line arguments.
        """

        parser.add_argument(
            "--path", default=pathlib.Path(), type=pathlib.Path, help="Working path"
        )
        parser.add_argument(
            "--config",
            default=pathlib.Path("hermes.toml"),
            type=pathlib.Path,
            help="Configuration file in TOML format",
        )

        plugin_args = parser.add_argument_group("Extra options")
        plugin_args.add_argument(
            "-O",
            nargs=2,
            action="append",
            default=[],
            metavar=("NAME", "VALUE"),
            dest="options",
            help="Configuration values to override hermes.toml options. "
            "NAME is the dotted name / path to the option in the TOML file, "
            "VALUE is the actual value.",
        )

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        """Initialize the command line arguments available for this specific HERMES sub-commands.

        You should override this method to add your custom arguments to the command line parser of
        the respective sub-command.

        :param command_parser: The command line sub-parser responsible for the HERMES sub-command.
        """

        pass

    def load_settings(self, args: argparse.Namespace):
        """Load settings from the configuration file (passed in from command line)."""

        toml_data = toml.load(args.path / args.config)
        self.root_settings = HermesCommand.settings_class.model_validate(toml_data)
        self.settings = getattr(self.root_settings, self.command_name)

    def patch_settings(self, args: argparse.Namespace):
        """Process command line options for the settings."""

        for key, value in args.options:
            target = self.settings
            sub_keys = key.split('.')
            for sub_key in sub_keys[:-1]:
                target = getattr(target, sub_key)

            # TODO: Transform the value accordingly before setting it
            setattr(target, sub_keys[-1], value)

    @abc.abstractmethod
    def __call__(self, args: argparse.Namespace):
        """Execute the HERMES sub-command.

        :param args: The namespace that was returned by the command line parser when reading the arguments.
        """

        pass


class HermesPlugin(abc.ABC):
    """Base class for all HERMES plugins."""

    settings_class: Optional[Type] = None

    @abc.abstractmethod
    def __call__(self, command: HermesCommand) -> None:
        """Execute the plugin.

        :param command: The command that triggered this plugin to run.
        """

        pass


class HermesHelpSettings(BaseModel):
    pass


class HermesHelpCommand(HermesCommand):
    """Show help page and exit."""

    command_name = "help"
    settings_class = HermesHelpSettings

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument(
            "subcommand",
            nargs="?",
            metavar="COMMAND",
            help="The HERMES sub-command to get help for.",
        )

    def __call__(self, args: argparse.Namespace) -> None:
        if args.subcommand:
            # When a sub-command is given, show its help page (i.e., by "running" the command with "-h" flag).
            self.parser.parse_args([args.subcommand, "-h"])
        else:
            # Otherwise, simply show the general help and exit (cleanly).
            self.parser.print_help()
            self.parser.exit()
