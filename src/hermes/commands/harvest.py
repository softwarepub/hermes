import collections
from pathlib import Path
import os
import json
import urllib.request
import typing as t


from ruamel.yaml import YAML
import jsonschema
from jsonschema.exceptions import ValidationError
import click
from cffconvert import Citation

from hermes.model.context import HermesContext
from hermes.model.errors import HermesValidationError


_CFF_VERSION = '1.2.0'


def convert_cff_to_codemeta(cff_file: str) -> t.Any:
    with open(cff_file, 'r') as infile:
        cffstr = infile.read()
        codemeta_str = Citation(cffstr).as_codemeta()
        return json.loads(codemeta_str)


def harvest_cff(click_ctx: click.Context, ctx: HermesContext):
    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')
    path = parent_ctx.params['path']

    # Get source files
    cff_file = get_single_cff(path)
    if not cff_file:
        raise HermesValidationError(f'{path} contains either no or more than 1 CITATION.cff file. Aborting harvesting '
                                    f'for this metadata source.')
    cff_dict = load_cff_from_file(cff_file)
    if not validate(cff_file, cff_dict):
        raise HermesValidationError(cff_file)
    # Convert to CodeMeta using cffconvert
    codemeta = convert_cff_to_codemeta(cff_file)
    ctx.update_from(codemeta, local_path=cff_file)


def build_path_str(absolute_path: collections.deque) -> str:
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


def validate(cff_file: str, cff_dict: t.Dict) -> bool:
    cff_schema_url = f'https://citation-file-format.github.io/{_CFF_VERSION}/schema.json'

    with urllib.request.urlopen(cff_schema_url) as cff_schema_response:
        schema_data = json.loads(cff_schema_response.read())
        validator = jsonschema.Draft7Validator(schema_data)
        errors = sorted(validator.iter_errors(cff_dict), key=lambda e: e.path)
        if len(errors) > 0:
            click.echo(f'{cff_file} is not valid according to {cff_schema_url}!')
            for error in errors:
                path_str = build_path_str(error.absolute_path)
                click.echo(f'    - Invalid input for path {path_str}.\n'
                           f'      Value: {error.instance} -> {error.message}')
            click.echo(f'    See the Citation File Format schema guide for further details: '
                       f'https://github.com/citation-file-format/citation-file-format/blob/{_CFF_VERSION}/schema'
                       f'-guide.md.')
            return False
        elif len(errors) == 0:
            click.echo(f'Found valid Citation File Format file at: {cff_file}')
            return True
    return False


def load_cff_from_file(cff_file: str) -> t.Any:
    with open(cff_file, 'r') as fi:
        yaml = YAML(typ='safe')
        yaml.constructor.yaml_constructors[u'tag:yaml.org,2002:timestamp'] = yaml.constructor.yaml_constructors[
            u'tag:yaml.org,2002:str']
        return yaml.load(fi)


def get_single_cff(path: str) -> str:
    # Find CFF files in directories and subdirectories
    files = find_file_paths('CITATION.cff', path)
    if len(files) == 1:
        return files[0]
    return ''


def find_file_paths(name: str, path: str) -> t.List[str]:
    files = []
    for dirpath, dirname, filename in os.walk(path):
        if name in filename:
            files.append(os.path.join(dirpath, name))
    return files
