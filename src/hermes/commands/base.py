# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import abc
import argparse
import logging
import pathlib
from importlib import metadata
from typing import Optional
from typing_extensions import Self

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import tomlkit


class HermesSettings(BaseSettings):
    """
    Root class for HERMES configuration model.

    Attributes:
        model_config (SettingsConfigDict): The settings config dict for the settings of hermes.
    """

    model_config = SettingsConfigDict(env_file_encoding='utf-8')


class HermesCommand(abc.ABC):
    """Base class for a HERMES workflow command.

    Attributes:
        command_name (str): (class attribute) Only defined here for highlighting, the value of the subclass is is used.
        settings_class (type): (class attribute) The settings class for the general hermes command settings
    """

    command_name: str = ""
    settings_class: type = HermesSettings

    def __init__(self: Self, parser: argparse.ArgumentParser) -> None:
        """
        Initialize a new instance of any HERMES command.

        Args:
            parser (ArgumentParser): The command line parser used for reading command line arguments.

        Returns:
            None:
        """
        self.parser = parser
        self.plugins = self.init_plugins()
        self.settings = None

        self.log = logging.getLogger(f"hermes.{self.command_name}")

    def init_plugins(self: Self) -> dict[str, type["HermesPlugin"]]:
        """
        Collect and initialize the plugins available for the HERMES command.

        Returns:
            dict[str, HermesPlugin]: A map mapping the plugin name to the plugin class for the current step.
        """

        # Collect all entry points for this group (i.e., all valid plug-ins for the step)
        entry_point_group = f"hermes.{self.command_name}"
        group_plugins = {}
        group_settings = {}

        for entry_point in metadata.entry_points(group=entry_point_group):
            plugin_cls = entry_point.load()

            group_plugins[entry_point.name] = plugin_cls
            if hasattr(plugin_cls, 'settings_class') and plugin_cls.settings_class is not None:
                group_settings[entry_point.name] = plugin_cls.settings_class

        self.derive_settings_class(group_settings)

        return group_plugins

    @classmethod
    def derive_settings_class(cls: type[Self], setting_types: dict[str, type["HermesPlugin"]]) -> None:
        """
        Build a new Pydantic data model class for configuration.

        This will create a new class that includes all settings from the plugins available.

        Args:
            settings_types (dict[str, type]): The settings classes for the plugins.

        Returns:
            None:

        Raises:
            ValueError: If the command has no settings.
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

    def init_common_parser(self: Self, parser: argparse.ArgumentParser) -> None:
        """
        Initialize the common command line arguments available for all HERMES sub-commands.

        Args:
            parser (ArgumentsParser): The base command line parser used as entry point when reading command line
                arguments.

        Returns:
            None:
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

    def init_command_parser(self: Self, command_parser: argparse.ArgumentParser) -> None:
        """
        Initialize the command line arguments available for this specific HERMES sub-commands.

        You should override this method to add your custom arguments to the command line parser of
        the respective sub-command.

        Args:
            command_parser (ArgumentParser): The command line sub-parser responsible for the HERMES sub-command.

        Returns:
            None:
        """

        pass

    def load_settings(self: Self, args: argparse.Namespace) -> None:
        """
        Load settings from the configuration file (passed in from command line).

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """

        toml_data = tomlkit.load((args.path / args.config).open()).unwrap()
        self.root_settings = HermesCommand.settings_class.model_validate(toml_data)
        self.settings = getattr(self.root_settings, self.command_name)

    def patch_settings(self: Self, args: argparse.Namespace) -> None:
        """
        Process command line options for the settings.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """

        for key, value in args.options:
            target = self.settings
            sub_keys = key.split('.')
            for sub_key in sub_keys[:-1]:
                target = getattr(target, sub_key)

            # TODO: Transform the value accordingly before setting it
            setattr(target, sub_keys[-1], value)

    @abc.abstractmethod
    def __call__(self: Self, args: argparse.Namespace) -> None:
        """Execute the HERMES sub-command.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """

        pass


class HermesPlugin(abc.ABC):
    """
    Base class for all HERMES plugins.

    Attributes:
        plugin_node: ...
        settings_class: The settings_class of the plugin.
    """

    pluing_node = None

    settings_class: Optional[type] = None

    @abc.abstractmethod
    def __call__(self: Self, command: HermesCommand) -> None:
        """
        Execute the plugin.

        Args:
            command (HermesCommand): The command that triggered this plugin to run.

        Returns:
            None:
        """

        pass


class HermesHelpSettings(BaseModel):
    """Intentionally empty settings class for the help command."""
    pass


class HermesHelpCommand(HermesCommand):
    """
    Show help page and exit.

    Attributes:
        command_name (str): (class attribute) The name of the command.
        settings_class (type): (class attribute) The settings class for general help settings.
    """

    command_name = "help"
    settings_class = HermesHelpSettings

    def init_command_parser(self: Self, command_parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for help command.

        Args:
            command_parser (ArgumentParser): The used argument parser.

        Returns:
            None:
        """
        command_parser.add_argument(
            "subcommand",
            nargs="?",
            metavar="COMMAND",
            help="The HERMES sub-command to get help for.",
        )

    def __call__(self: Self, args: argparse.Namespace) -> None:
        """
        Execute the hermes command `self`.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """
        if args.subcommand:
            # When a sub-command is given, show its help page (i.e., by "running" the command with "-h" flag).
            self.parser.parse_args([args.subcommand, "-h"])
        else:
            # Otherwise, simply show the general help and exit (cleanly).
            self.parser.print_help()
            self.parser.exit()


class HermesVersionSettings(BaseModel):
    """Intentionally empty settings class for the version command."""
    pass


class HermesVersionCommand(HermesCommand):
    """
    Show HERMES version and exit.

    Attributes:
        command_name (str): (class attribute) The name of the command.
        settings_class (type): (class attribute) The settings class for general help settings.
    """

    command_name = "version"
    settings_class = HermesVersionSettings

    def load_settings(self: Self, args: argparse.Namespace) -> None:
        """
        Pass loading settings as not necessary for this command.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """
        pass

    def __call__(self: Self, args: argparse.Namespace) -> None:
        """
        Execute the hermes command `self`.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """
        self.log.info(metadata.version("hermes"))
        self.parser.exit()
