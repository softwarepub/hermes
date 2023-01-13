# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import glob
import json
import pathlib
import typing as t

import click
from convert_codemeta.validate import validate_codemeta

from hermes.commands.harvest import util
from hermes.model.context import HermesHarvestContext
from hermes.model.errors import HermesValidationError


def harvest_codemeta(click_ctx: click.Context, ctx: HermesHarvestContext):
    """
    Implementation of a harvester that provides data from a codemeta.json file format.

    :param click_ctx: Click context that this command was run inside (might be used to extract command line arguments).
    :param ctx: The harvesting context that should contain the provided metadata.
    """
    # Get project path
    path = util.get_project_path(click_ctx)

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
    ctx.update_from(codemeta, local_path=str(codemeta_file))


def _validate(codemeta_file: pathlib.Path) -> bool:
    with open(codemeta_file, 'r') as fi:
        try:
            codemeta_json = json.load(fi)
        except json.decoder.JSONDecodeError as jde:
            raise HermesValidationError(f'CodeMeta file at {codemeta_file} cannot be decoded into JSON.', jde)
    return validate_codemeta(codemeta_json)


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
