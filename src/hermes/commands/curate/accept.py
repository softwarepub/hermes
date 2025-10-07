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
    def __call__(self, command):
        ctx = CodeMetaContext()
        process_output = ctx.hermes_dir / "process" / (ctx.hermes_name + ".json")

        os.makedirs(ctx.hermes_dir / "curate", exist_ok=True)
        shutil.copy(
            process_output, ctx.hermes_dir / "curate" / (ctx.hermes_name + ".json")
        )
