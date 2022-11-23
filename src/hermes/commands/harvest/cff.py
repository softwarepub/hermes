# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import collections
import glob
import os
import json
import pathlib
import urllib.request
import typing as t


from ruamel.yaml import YAML
import jsonschema
import click
from cffconvert import Citation

from hermes.model.context import HermesHarvestContext
from hermes.model.errors import HermesValidationError

# TODO: should this be configurable via a CLI option?
_CFF_VERSION = '1.2.0'


def harvest_cff(click_ctx: click.Context, ctx: HermesHarvestContext):
    """
    Implementation of a harvester that provides data from CFF in Codemeta format.

    :param click_ctx: Click context that this command was run inside (might be used to extract command line arguments).
    :param ctx: The harvesting context that should contain the provided metadata.
    """
    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')
    path = parent_ctx.params['path']

    # Get source files
    cff_file = _get_single_cff(path)
    if not cff_file:
        raise HermesValidationError(f'{path} contains either no or more than 1 CITATION.cff file. Aborting harvesting '
                                    f'for this metadata source.')

    # Read the content
    cff_data = cff_file.read_text()

    # Validate the content to be correct CFF
    cff_dict = _load_cff_from_file(cff_data)
    if not _validate(cff_file, cff_dict):
        raise HermesValidationError(cff_file)

    # Convert to CodeMeta using cffconvert
    codemeta = _convert_cff_to_codemeta(cff_data)
    ctx.update_from(codemeta, local_path=str(cff_file))


def _load_cff_from_file(cff_data: str) -> t.Any:
    yaml = YAML(typ='safe')
    yaml.constructor.yaml_constructors[u'tag:yaml.org,2002:timestamp'] = yaml.constructor.yaml_constructors[
        u'tag:yaml.org,2002:str']
    return yaml.load(cff_data)


def _convert_cff_to_codemeta(cff_data: str) -> t.Any:
    codemeta_str = Citation(cff_data).as_codemeta()
    return json.loads(codemeta_str)


def _validate(cff_file: pathlib.Path, cff_dict: t.Dict) -> bool:
    cff_schema_url = f'https://citation-file-format.github.io/{_CFF_VERSION}/schema.json'

    # TODO: we should ship the schema we reference to by default to avoid unnecessary network traffic.
    #       If the requested version is not already downloaded, go ahead and download it.
    with urllib.request.urlopen(cff_schema_url) as cff_schema_response:
        schema_data = json.loads(cff_schema_response.read())

    validator = jsonschema.Draft7Validator(schema_data)
    errors = sorted(validator.iter_errors(cff_dict), key=lambda e: e.path)
    if len(errors) > 0:
        click.echo(f'{cff_file} is not valid according to {cff_schema_url}!')
        for error in errors:
            path_str = _build_nodepath_str(error.absolute_path)
            click.echo(f'    - Invalid input for path {path_str}.\n'
                       f'      Value: {error.instance} -> {error.message}')
        click.echo(f'    See the Citation File Format schema guide for further details: '
                   f'https://github.com/citation-file-format/citation-file-format/blob/{_CFF_VERSION}/schema'
                   f'-guide.md.')
        return False
    elif len(errors) == 0:
        click.echo(f'Found valid Citation File Format file at: {cff_file}')
        return True


def _get_single_cff(path: pathlib.Path) -> t.Optional[pathlib.Path]:
    # Find CFF files in directories and subdirectories
    # TODO: Do we really want to search recursive? CFF convention is the file should be at the topmost dir,
    #       which is given via the --path arg. Maybe add another option to enable pointing to a single file?
    #       (So this stays "convention over configuration")
    files = glob.glob(str(path / '**' / 'CITATION.cff'), recursive=True)
    if len(files) == 1:
        return pathlib.Path(files[0])
    # TODO: Shouldn't we log/echo the found CFF files so a user can debug/cleanup?
    # TODO: Do we want to hand down a logging instance via Hermes context or just encourage
    #       peeps to use the Click context?
    return None


def _build_nodepath_str(absolute_path: collections.deque) -> str:
    # Path deque starts with field name, then index, then field name, etc.
    path_str = "'"
    for index, value in enumerate(absolute_path):
        if index == 0:  # First value
            path_str += f'{value}'
        elif index % 2 == 0:  # value is a field name
            path_str += f' -> {value}'
        else:  # Value is an index
            path_str += f' {int(value) + 1}'  # Use index starting at 1
    path_str += "'"
    return path_str
