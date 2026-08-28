# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import typing as t
from datetime import datetime
import tempfile
import pathlib
from hermes import logger

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context import HermesContext, HermesHarvestContext
from hermes.model.errors import HermesValidationError, MergeError
from hermes.commands.harvest.util.token import update_token_to_toml, remove_token_from_toml
from hermes.commands.harvest.util.clone import clone_repository

class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> t.Tuple[t.Dict, t.Dict]:
        pass


class _HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = _HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        ctx = HermesContext()

        # Initialize the harvest cache directory here to indicate the step ran
        ctx.init_cache("harvest")

        logger.init_logging()
        log = logger.getLogger("hermes.cli")

        if args.url:
            with tempfile.TemporaryDirectory(dir=".") as temp_dir:
                temp_path = pathlib.Path(temp_dir)
                log.info(f"Cloning repository {args.url} into {temp_path}")
                
                try:
                    clone_repository(args.url, temp_path, recursive=True, depth=1, filter_blobs=True, sparse=False)
                except Exception as exc:
                    print("ERROR:", exc)
                args.path = temp_path  # Overwrite args.path to temp directory

                if args.token:
                    update_token_to_toml(args.token)
                self._harvest(ctx)
                if args.token:
                    remove_token_from_toml('hermes.toml')
        else:
            self._harvest(ctx)
            
    def _harvest(self, ctx: HermesContext) -> None:
        """Harvest metadata from configured sources using plugins."""
        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]()
                harvested_data, tags = plugin_func(self)

                with HermesHarvestContext(ctx, plugin_name) as harvest_ctx:
                    harvest_ctx.update_from(harvested_data,
                                            plugin=plugin_name,
                                            timestamp=datetime.now().isoformat(), **tags)
                    for _key, ((_value, _tag), *_trace) in harvest_ctx._data.items():
                        if any(v != _value and t == _tag for v, t in _trace):
                            raise MergeError(_key, None, _value)

            except KeyError as e:
                self.log.error("Plugin '%s' not found.", plugin_name)
                self.errors.append(e)

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
                self.errors.append(e)
