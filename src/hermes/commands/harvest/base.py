# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import typing as t

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context_manager import HermesContext
from hermes.model.errors import HermesValidationError, MergeError
from hermes.model.ld_utils import bundled_document_loader, jsonld_dict


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

        # Initialize the harvest cache directory here to indicate the step ran
        ctx = HermesContext()
        ctx.prepare_step('harvest')

        for plugin_name in self.settings.sources:
            try:
                # Load plugin and run the harvester
                plugin_func = self.plugins[plugin_name]()
                harvested_data, tags = plugin_func(self)

                # Ensure we have a jsonld_dict here to allow expansion
                if not isinstance(harvested_data, jsonld_dict):
                    harvested_data = jsonld_dict(**harvested_data)

                # Transform the graph into a canoncial form
                expanded_data, jsonld_context = harvested_data.expand()

                with ctx[plugin_name] as plugin_ctx:
                    plugin_ctx['data'] = harvested_data
                    plugin_ctx['jsonld'] = expanded_data
                    plugin_ctx['context'] = jsonld_context
                    plugin_ctx['tags'] = tags

            except KeyError as e:
                self.log.error("Plugin '%s' not found.", plugin_name)
                self.errors.append(e)

            #except HermesHarvestError as e:
            #    self.log.error("Harvesting %s failed: %s", plugin_name, e)
            #    self.errors.append(e)

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
                self.errors.append(e)

        ctx.finalize_step('harvest')
