# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel

import json

import click

from hermes import config
from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def dummy_noop(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def map_metadata(click_ctx: click.Context, ctx: CodeMetaContext):
    ctx.update(ContextPath.parse('deposit.file'), ctx['codemeta'])


def publish(click_ctx: click.Context, ctx: CodeMetaContext):
    file_config = config.get("deposit").get("file", {})
    output_data = ctx['deposit.file']

    with open(file_config.get('filename', 'hermes.json'), 'w') as deposition_file:
        json.dump(output_data, deposition_file)
