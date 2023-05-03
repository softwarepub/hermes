# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Oliver Bertuch

import json
import logging
import os
import shutil
from importlib import metadata

import click

from hermes import config
from hermes.error import MisconfigurationError
from hermes.model.context import HermesContext, HermesHarvestContext, CodeMetaContext
from hermes.model.errors import MergeError
from hermes.model.path import ContextPath


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

    # Initialize the harvest cache directory here to indicate the step ran
    ctx.init_cache("harvest")

    # Get all harvesters
    harvest_config = config.get("harvest")
    harvester_names = harvest_config.get('from', [ep.name for ep in metadata.entry_points(group='hermes.harvest')])

    for harvester_name in harvester_names:
        harvesters = metadata.entry_points(group='hermes.harvest', name=harvester_name)
        if not harvesters:
            _log.warning("- Harvester %s selected but not found.", harvester_name)
            continue

        harvester, *_ = harvesters
        _log.info("- Running harvester %s", harvester.name)

        _log.debug(". Loading harvester from %s", harvester.value)
        harvest = harvester.load()

        with HermesHarvestContext(ctx, harvester, harvest_config.get(harvester.name, {})) as harvest_ctx:
            harvest(click_ctx, harvest_ctx)
            for _key, ((_value, _tag), *_trace) in harvest_ctx._data.items():
                if any(v != _value and t == _tag for v, t in _trace):
                    raise MergeError(_key, None, _value)

        _log.info('')
    audit_log.info('')


@click.group(invoke_without_command=True)
@click.pass_context
def process(click_ctx: click.Context):
    """
    Process metadata and prepare it for deposition
    """
    _log = logging.getLogger('cli.process')

    audit_log = logging.getLogger('audit')
    audit_log.info("# Metadata processing")

    ctx = CodeMetaContext()

    if not (ctx.hermes_dir / "harvest").exists():
        _log.error("You must run the harvest command before process")
        click_ctx.exit(1)

    # Get all harvesters
    harvest_config = config.get("harvest")
    harvester_names = harvest_config.get('from', [ep.name for ep in metadata.entry_points(group='hermes.harvest')])

    for harvester_name in harvester_names:
        harvesters = metadata.entry_points(group='hermes.harvest', name=harvester_name)
        if not harvesters:
            _log.warning("- Harvester %s selected but not found.", harvester_name)
            continue

        harvester, *_ = harvesters
        audit_log.info("## Process data from %s", harvester.name)

        harvest_context = HermesHarvestContext(ctx, harvester, {})
        try:
            harvest_context.load_cache()
        # when the harvest step ran, but there is no cache file, this is a serious flaw
        except FileNotFoundError:
            _log.warning("No output data from harvester %s found, skipping", harvester.name)
            continue

        preprocessors = metadata.entry_points(group='hermes.preprocess', name=harvester.name)
        for preprocessor in preprocessors:
            _log.debug(". Loading context preprocessor %s", preprocessor.value)
            preprocess = preprocessor.load()

            _log.debug(". Apply preprocessor %s", preprocessor.value)
            preprocess(ctx, harvest_context)

        ctx.merge_from(harvest_context)
        ctx.merge_contexts_from(harvest_context)
        _log.info('')
    audit_log.info('')

    if ctx._errors:
        audit_log.error('!!! warning "Errors during merge"')

        for ep, error in ctx._errors:
            audit_log.info('    - %s: %s', ep.name, error)

    tags_path = ctx.get_cache('process', 'tags', create=True)
    with tags_path.open('w') as tags_file:
        json.dump(ctx.tags, tags_file, indent=2)

    ctx.prepare_codemeta()

    with open(ctx.get_cache("process", "codemeta", create=True), 'w') as codemeta_file:
        json.dump(ctx._data, codemeta_file, indent=2)

    logging.shutdown()


@click.group(invoke_without_command=True)
def curate():
    ctx = CodeMetaContext()
    os.makedirs(ctx.hermes_dir / 'curate', exist_ok=True)
    shutil.copy(ctx.hermes_dir / 'process' / 'codemeta.json', ctx.hermes_dir / 'curate' / 'codemeta.json')


@click.group(invoke_without_command=True)
@click.option(
    "--auth-token", envvar="HERMES_DEPOSITION_AUTH_TOKEN",
    help="Token used to authenticate the user with the target deposition platform. "
         "Can be passed on the command line or as an environment variable."
)
@click.option(
    "--file", "-f", multiple=True, required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Files to be uploaded on the target deposition platform. "
         "This option may be passed multiple times."
)
@click.pass_context
def deposit(click_ctx: click.Context, auth_token, file):
    """
    Deposit processed (and curated) metadata.
    """
    click.echo("Metadata deposition")
    _log = logging.getLogger("cli.deposit")

    ctx = CodeMetaContext()

    codemeta_file = ctx.get_cache("curate", "codemeta")
    if not codemeta_file.exists():
        _log.error("You must run the 'curate' command before deposit")
        click_ctx.exit(1)

    # Loading the data into the "codemeta" field is a temporary workaround used because
    # the CodeMetaContext does not provide an update_from method. Eventually we want the
    # the context to contain `{**data}` rather than `{"codemeta": data}`. Then, for
    # additional data, the hermes namespace should be used.
    codemeta_path = ContextPath("codemeta")
    with open(codemeta_file) as codemeta_fh:
        ctx.update(codemeta_path, json.load(codemeta_fh))

    deposit_config = config.get("deposit")

    # The platform to which we want to deposit the (meta)data
    deposition_platform = deposit_config.get("target", "invenio")
    # The metadata mapping logic for the target platform
    deposition_mapping = deposit_config.get("mapping", "invenio")

    # Prepare the deposit
    deposit_preparator_entrypoints = metadata.entry_points(
        group="hermes.prepare_deposit",
        name=deposition_platform
    )
    if deposit_preparator_entrypoints:
        deposit_preparator = deposit_preparator_entrypoints[0].load()
        try:
            deposit_preparator(click_ctx, ctx)
        except (RuntimeError, MisconfigurationError) as e:
            _log.error(e)
            click_ctx.exit(1)

    # Map metadata onto target schema
    metadata_mapping_entrypoints = metadata.entry_points(
        group="hermes.metadata_mapping",
        name=deposition_mapping
    )
    if metadata_mapping_entrypoints:
        metadata_mapping = metadata_mapping_entrypoints[0].load()
        metadata_mapping(click_ctx, ctx)

    # Make deposit: Update metadata, upload files, publish
    # TODO: Do publish step manually? This would allow users to check the deposition on
    # the site and decide whether they are happy with it.
    deposition_entrypoints = metadata.entry_points(
        group="hermes.deposit",
        name=deposition_platform
    )
    if deposition_entrypoints:
        deposition = deposition_entrypoints[0].load()
        deposition(click_ctx, ctx)


@click.group(invoke_without_command=True)
def postprocess():
    """
    Postprocess metadata after deposition
    """
    click.echo("Post-processing")


@click.group(invoke_without_command=True)
def clean():
    """
    Remove cached data.
    """
    audit_log = logging.getLogger('audit')
    audit_log.info("# Cleanup")

    # Create Hermes context (i.e., all collected metadata for all stages...)
    ctx = HermesContext()
    ctx.purge_caches()
