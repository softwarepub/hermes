# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json

from hermes import config
from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def dummy_noop(ctx: CodeMetaContext):
    pass


def map_metadata(ctx: CodeMetaContext):
    ctx.update(ContextPath.parse("deposit.file"), ctx["codemeta"])


def publish(ctx: CodeMetaContext):
    file_config = config.get("deposit").get("file", {})
    output_data = ctx["deposit.file"]

    with open(file_config.get("filename", "hermes.json"), "w") as deposition_file:
        json.dump(output_data, deposition_file)
