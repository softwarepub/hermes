# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
from typing import Union

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.api import SoftwareMetadata
from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesContextError
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict


class HermesProcessPlugin(HermesPlugin):
    """ Base plugin that defines additional merge strategies."""

    def __call__(self, command: HermesCommand) -> dict[Union[str, None], dict[Union[str, None], MergeAction]]:
        pass


class ProcessSettings(BaseModel):
    """Generic deposition settings."""

    plugins: list = []


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"
    settings_class = ProcessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        ctx = HermesContext()
        merged_doc = ld_merge_dict([{}])

        # add the strategies from the plugins
        for plugin_name in reversed(self.settings.plugins):
            additional_strategies = self.plugins[plugin_name]()(self)
            merged_doc.add_strategy(additional_strategies)

        # Get all harvesters
        harvester_names = self.root_settings.harvest.sources

        ctx.prepare_step('harvest')
        for harvester in harvester_names:
            self.log.info("## Process data from %s", harvester)
            try:
                metadata = SoftwareMetadata.load_from_cache(ctx, harvester)
            except HermesContextError as e:
                self.log.error("Error while trying to load data from harvest plugin '%s': %s", harvester, e)
                self.errors.append(e)
                continue
            merged_doc.update(metadata)
        ctx.finalize_step("harvest")

        ctx.prepare_step("process")
        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = {"@context": merged_doc.full_context}
            result_ctx["expanded"] = merged_doc.ld_value
        ctx.finalize_step("process")
