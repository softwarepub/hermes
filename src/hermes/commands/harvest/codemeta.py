import glob
import json
import pathlib
import typing as t

import click

from hermes.model.context import HermesHarvestContext
from hermes.model.errors import HermesValidationError


def harvest_codemeta(click_ctx: click.Context, ctx: HermesHarvestContext):
    """
    Implementation of a harvester that provides data from a codemeta.json file format.

    :param click_ctx: Click context that this command was run inside (might be used to extract command line arguments).
    :param ctx: The harvesting context that should contain the provided metadata.
    """
    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')
    path = parent_ctx.params['path']

    # Get source files
    codemeta_file = _get_single_codemeta(path)
    if not codemeta_file:
        raise HermesValidationError(f'{path} contains either no or more than 1 codemeta.json file. Aborting harvesting '
                                    f'for this metadata source.')

    # Read the content
    codemeta_str = codemeta_file.read_text()

    if not _validate(codemeta_file):
        raise HermesValidationError(codemeta_file)

    codemeta = json.loads(codemeta_str)
    print(codemeta)
    ctx.update_from(codemeta, local_path=str(codemeta_file))


def _validate(codemeta_file: pathlib.Path) -> bool:
    # TODO: Implement
    return True


def _get_single_codemeta(path: pathlib.Path) -> t.Optional[pathlib.Path]:
    # Find CodeMeta files in directories and subdirectories
    # TODO: Do we really want to search recursive? Maybe add another option to enable pointing to a single file?
    #       (So this stays "convention over configuration")
    files = glob.glob(str(path / '**' / 'codemeta.json'), recursive=True)
    if len(files) == 1:
        return pathlib.Path(files[0])
    # TODO: Shouldn't we log/echo the found CFF files so a user can debug/cleanup?
    # TODO: Do we want to hand down a logging instance via Hermes context or just encourage
    #       peeps to use the Click context?
    return None
