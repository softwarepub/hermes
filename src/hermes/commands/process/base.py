# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import json
import sys

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context import HermesHarvestContext, CodeMetaContext


class HermesProcessPlugin(HermesPlugin):

    pass


class ProcessSettings(BaseModel):
    """Generic deposition settings."""

    pass


class HermesProcessCommand(HermesCommand):
    """ Process the collected metadata into a common dataset. """

    command_name = "process"
    settings_class = ProcessSettings

    def __call__(self, args: argparse.Namespace) -> None:
        self.args = args
        ctx = CodeMetaContext()

        if not (ctx.hermes_dir / "harvest").exists():
            self.log.error("You must run the harvest command before process")
            sys.exit(1)

        # Get all harvesters
        harvester_names = self.root_settings.harvest.sources
        harvester_names.reverse()   # Switch order for priority handling

        for harvester in harvester_names:
            self.log.info("## Process data from %s", harvester)

            harvest_context = HermesHarvestContext(ctx, harvester, {})
            try:
                harvest_context.load_cache()
            # when the harvest step ran, but there is no cache file, this is a serious flaw
            except FileNotFoundError:
                self.log.warning("No output data from harvester %s found, skipping", harvester)
                continue

            ctx.merge_from(harvest_context)
            ctx.merge_contexts_from(harvest_context)

        if ctx._errors:
            self.log.error('!!! warning "Errors during merge"')

            for ep, error in ctx._errors:
                self.log.info("    - %s: %s", ep.name, error)

        tags_path = ctx.get_cache('process', 'tags', create=True)
        with tags_path.open('w') as tags_file:
            json.dump(ctx.tags, tags_file, indent=2)

        ctx.prepare_codemeta()

        with open(ctx.get_cache("process", ctx.hermes_name, create=True), 'w') as codemeta_file:
            json.dump(ctx._data, codemeta_file, indent=2)
