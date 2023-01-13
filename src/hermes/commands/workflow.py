# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape

import json
import logging
from importlib import metadata

import click

from hermes.model.context import HermesContext, HermesHarvestContext, CodeMetaContext
from hermes.model.errors import MergeError


@click.group(invoke_without_command=True)
@click.pass_context
def harvest(click_ctx: click.Context):
    """
    Automatic harvest of metadata
    """
    _log = logging.getLogger('cli.harvest')
    audit_log = logging.getLogger('audit')
    audit_log.info("# Metadata harvesting")

    # Create Hermes context (i.e., all collected metadata for all stages...)
    ctx = HermesContext()

    # Get all harvesters
    harvesters = metadata.entry_points(group='hermes.harvest')
    for harvester in harvesters:
        _log.info("- Running harvester %s", harvester.name)

        _log.debug(". Loading harvester from %s", harvester.value)
        harvest = harvester.load()

        with HermesHarvestContext(ctx, harvester) as harvest_ctx:
            harvest(click_ctx, harvest_ctx)
            for _key, ((_value, _tag), *_trace) in harvest_ctx._data.items():
                if any(v != _value and t == _tag for v, t in _trace):
                    raise MergeError(_key, None, _value)
        _log.info('')
    audit_log.info('')


@click.group(invoke_without_command=True)
def process():
    """
    Process metadata and prepare it for deposition
    """
    _log = logging.getLogger('cli.process')

    audit_log = logging.getLogger('audit')
    audit_log.info("# Metadata processing")

    ctx = CodeMetaContext()

    harvesters = metadata.entry_points(group='hermes.harvest')
    for harvester in harvesters:
        audit_log.info("## Process data from %s", harvester.name)

        harvest_context = HermesHarvestContext(ctx, harvester)
        harvest_context.load_cache()

        processors = metadata.entry_points(group='hermes.preprocess', name=harvester.name)
        for processor in processors:
            _log.debug(". Loading context processor %s", processor.value)
            process = processor.load()

            _log.debug(". Apply processor %s", processor.value)
            process(ctx, harvest_context)

        ctx.merge_from(harvest_context)
        _log.info('')
    audit_log.info('')

    if ctx._errors:
        audit_log.error('!!! warning "Errors during merge"')

        for ep, error in ctx._errors:
            audit_log.info('    - %s: %s', ep.name, error)

    tags_path = ctx.get_cache('process', 'tags', create=True)
    with tags_path.open('w') as tags_file:
        json.dump(ctx.tags, tags_file, indent='  ')

    with open('codemeta.json', 'w') as codemeta_file:
        json.dump(ctx._data, codemeta_file, indent='  ')

    logging.shutdown()


@click.group(invoke_without_command=True)
def deposit():
    """
    Deposit processed (and curated) metadata
    """
    click.echo("Metadata deposition")

    # local import that can be removed later
    from hermes.model.path import ContextPath

    ctx = CodeMetaContext()

    # TODO: Remove this
    deposition_platform_path = ContextPath("depositionPlatorm")
    deposit_invenio_path = ContextPath.parse("deposit.invenio")

    # TODO: Remove this
    # Which kind of platform do we target here? For now, we just put "invenio" there.
    ctx.update(deposition_platform_path, "invenio")

    # TODO: Remove this
    # There are many Invenio instances. For now, we just use Zenodo as a default.
    ctx.update(deposit_invenio_path["siteUrl"], "https://zenodo.org")
    ctx.update(
        deposit_invenio_path["recordSchemaPath"],
        "api/schemas/records/record-v1.0.0.json"
    )

    # The platform to which we want to deposit the (meta)data
    # TODO: Get this from config
    deposition_platform = ctx["depositionPlatorm"]

    # Prepare the deposit
    deposit_preparator_entrypoints = metadata.entry_points(
        group="hermes.prepare_deposit",
        name=deposition_platform
    )
    if deposit_preparator_entrypoints:
        deposit_preparator = deposit_preparator_entrypoints[0].load()
        deposit_preparator(ctx)

    # TODO: Metadata mapping

    # TODO: Deposit


@click.group(invoke_without_command=True)
def postprocess():
    """
    Postprocess metadata after deposition
    """
    click.echo("Post-processing")
