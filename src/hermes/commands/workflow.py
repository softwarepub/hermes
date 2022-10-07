# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

from importlib import metadata

import click

from hermes.model.context import HermesContext, HermesHarvestContext


@click.group(invoke_without_command=True)
@click.pass_context
def harvest(click_ctx: click.Context):
    """
    Automatic harvest of metadata
    """
    click.echo("Metadata harvesting")

    # Create Hermes context (i.e., all collected metadata for all stages...)
    ctx = HermesContext()

    # Get all harvesters
    harvesters = metadata.entry_points(group='hermes.harvest')
    for harvester in harvesters:
        with HermesHarvestContext(ctx, harvester) as harvest_ctx:
            harvest = harvester.load()
            harvest(click_ctx, harvest_ctx)


@click.group(invoke_without_command=True)
def process():
    """
    Process metadata and prepare it for deposition
    """
    click.echo("Metadata processing")


@click.group(invoke_without_command=True)
def deposit():
    """
    Deposit processed (and curated) metadata
    """
    click.echo("Metadata deposition")


@click.group(invoke_without_command=True)
def post():
    """
    Post-process metadata after deposition
    """
    click.echo("Post-processing")
