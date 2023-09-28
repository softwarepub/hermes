import json

import click

from hermes import config
from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def prepare(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def prepare_metadata(click_ctx: click.Context, ctx: CodeMetaContext):
    ctx.update(ContextPath.parse('deposit.file'), ctx['codemeta'])


def create_initial_version(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def create_new_version(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def update_metadata(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def delete_artifacts(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def upload_artifacts(click_ctx: click.Context, ctx: CodeMetaContext):
    pass


def publish(click_ctx: click.Context, ctx: CodeMetaContext):
    file_config = config.get("deposit").get("file", {})
    output_data = ctx['deposit.file']

    with open(file_config.get('filename', 'hermes.json'), 'w') as deposition_file:
        json.dump(output_data, deposition_file)
