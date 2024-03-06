# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import typing as t
from datetime import datetime

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context import HermesContext, HermesHarvestContext
from hermes.model.errors import HermesValidationError, MergeError


class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> t.Tuple[t.Dict, t.Dict]:
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        ctx = HermesContext()

        # Initialize the harvest cache directory here to indicate the step ran
        ctx.init_cache("harvest")

        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]()
                harvested_data, tags = plugin_func(self)
                print(harvested_data)
                with HermesHarvestContext(
                        ctx, plugin_name
                ) as harvest_ctx:
                    harvest_ctx.update_from(harvested_data,
                                            plugin=plugin_name,
                                            timestamp=datetime.now().isoformat(), **tags)
                    for _key, ((_value, _tag), *_trace) in harvest_ctx._data.items():
                        if any(v != _value and t == _tag for v, t in _trace):
                            raise MergeError(_key, None, _value)

            except KeyError:
                self.log.error("Plugin '%s' not found.", plugin_name)

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
