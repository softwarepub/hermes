# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse

from pydantic import BaseModel

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context_manager import HermesContext
from hermes.model.merge.container import ld_merge_dict
from hermes.model.types import ld_dict, ld_context


iri = ld_context.iri_map


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
        ctx = HermesContext()
        ctx.prepare_step("process")

        merged_doc = ld_merge_dict([{}], self.prov_doc)

        # Get all harvesters
        harvester_names = self.root_settings.harvest.sources

        ctx.prepare_step('harvest')
        with ctx["result"] as harvest_ctx:
            prov_data = harvest_ctx["prov"]
            prov_graph = ld_dict.from_dict({"hermes-rt:graph": prov_data, "qcontext": prov_data["@context"]})
            self.prov_doc.extend(prov_graph["hermes-rt:graph"])

        for harvester in harvester_names:
            self.log.info("## Process data from %s", harvester)

            with ctx[harvester] as harvest_ctx:
                input_doc = ld_dict(
                    harvest_ctx["expanded"],
                    context=harvest_ctx["context"]["@context"])
                merged_doc.update(input_doc)

        ctx.finalize_step("harvest")

        with ctx["result"] as result_ctx:
            result_ctx["codemeta"] = merged_doc.compact()
            result_ctx["context"] = merged_doc.context
            result_ctx["expanded"] = merged_doc.ld_value
            result_ctx["prov"] = self.prov_doc.compact()

        ctx.finalize_step("process")
