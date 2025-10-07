# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR), 2025 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape

import os
import shutil

from hermes.commands.curate.base import BaseCuratePlugin
from hermes.model.context import CodeMetaContext


class AcceptCuratePlugin(BaseCuratePlugin):
    """Accept plugin for the curation step.

    This plugin creates a positive curation result, i.e. it accepts the produced
    metadata as correct and lets the execution continue without human intervention. It
    also copies the metadata produced in the process step to the "curate" directory.
    """

    def get_decision(self):
        """Simulate positive curation result."""
        return True

    def process_decision_positive(self):
        """In case of positive curation result, copy files to next step."""
        ctx = CodeMetaContext()
        process_output = ctx.hermes_dir / "process" / (ctx.hermes_name + ".json")

        os.makedirs(ctx.hermes_dir / "curate", exist_ok=True)
        shutil.copy(
            process_output, ctx.hermes_dir / "curate" / (ctx.hermes_name + ".json")
        )
