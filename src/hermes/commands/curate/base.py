# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import json
import os
import shutil
import sys

from pydantic import BaseModel

from hermes.commands.base import HermesCommand
from hermes.model.context_manager import HermesContext
from hermes.model.types import ld_dict, ld_list


class CurateSettings(BaseModel):
    """Generic deposition settings."""

    pass


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"
    settings_class = CurateSettings

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:

        self.log.info("# Metadata curation")

        ctx = HermesContext()
        ctx.prepare_step("curate")

        ctx.prepare_step("process")
        with ctx["result"] as process_ctx:
            expanded_data = process_ctx["expanded"]
            context_data = process_ctx["context"]
            prov_data = process_ctx["prov"]
        ctx.finalize_step("process")

        prov_doc = ld_dict.from_dict({"hermes-rt:graph": prov_data, "@context": prov_data["@context"]})

        nodes = {}
        edges = {}

        for node in prov_doc["hermes-rt:graph"]:
            nodes[node["@id"]] = node

            for rel in ('schema:isPartOf', "schema:hasPart", "prov:used", "prov:generated", "prov:wasStartedBy"):
                if rel in node:
                    rel_ids = node[rel]
                    if not isinstance(rel_ids, ld_list):
                        rel_ids = [rel_ids]
                    edges[rel] = edges.get(rel, []) + [(node["@id"], rel_id) for rel_id in rel_ids]

        with ctx["result"] as curate_ctx:
            curate_ctx["expanded"] = expanded_data
            curate_ctx["context"] = context_data

        ctx.finalize_step("curate")
