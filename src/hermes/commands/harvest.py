import collections
from pathlib import Path
import os
import json
import urllib.request

from ruamel.yaml import YAML
import jsonschema
from jsonschema.exceptions import ValidationError
import click

from hermes.model.context import HermesContext
from hermes.model.errors import HermesValidationError


_CFF_VERSION = '1.2.0'


def harvest_cff(click_ctx: click.Context, ctx: HermesContext):
    # Get the parent context (every subcommand has its own context with the main click context as parent)
    parent_ctx = click_ctx.parent
    path = parent_ctx.params['path']

    # Get source files
    cff_file = get_single_cff(path)
    if cff_file is None:
        click.echo(f'{path} contains either no or more than 1 CITATION.cff file. Aborting harvesting for this '
                   f'metadata source.')
        return 1
    else:
        if not validate(cff_file):
            return 1
        else:
            click.echo(f'Hello CFF harvester for {cff_file}')

    # # Load
    # cff = read_cff(source)
    #
    # # Convert
    # authors = cff.get('authors')
    #
    # if authors:
    #     for author in authors:
    #         ctx.update('author', author, src=source)


def read_cff(source):
    return {}


def build_path_str(absolute_path: collections.deque):
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


def validate(cff_file):
    cff_schema_url = f'https://citation-file-format.github.io/{_CFF_VERSION}/schema.json'
    with open(cff_file, 'r') as fi:
        # Convert to Python object
        yaml = YAML(typ='safe')
        yaml.constructor.yaml_constructors[u'tag:yaml.org,2002:timestamp'] = yaml.constructor.yaml_constructors[
            u'tag:yaml.org,2002:str']
        yml_data = yaml.load(fi)

        with urllib.request.urlopen(cff_schema_url) as cff_schema_response:
            schema_data = json.loads(cff_schema_response.read())
            validator = jsonschema.Draft7Validator(schema_data)
            errors = sorted(validator.iter_errors(yml_data), key=lambda e: e.path)
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
                click.echo(f'{cff_file} is valid')
                return True


def get_single_cff(paths):
    # Find CFF files in directories and subdirectories
    for path in paths:
        files = find_file_paths('CITATION.cff', path)
        if len(files) == 1:
            return files[0]
        else:
            return None


def find_file_paths(name, path):
    files = []
    for dirpath, dirname, filename in os.walk(path):
        if name in filename:
            files.append(os.path.join(dirpath, name))
    return files
