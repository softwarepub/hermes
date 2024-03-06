# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import json
import logging
import pathlib
import urllib.request
import typing as t

from pydantic import BaseModel
from ruamel.yaml import YAML
import jsonschema
from cffconvert import Citation

from hermes.model.context import ContextPath
from hermes.model.errors import HermesValidationError
from hermes.commands.harvest.base import HermesHarvestPlugin, HermesHarvestCommand


# TODO: should this be configurable via a CLI option?
_CFF_VERSION = '1.2.0'

_log = logging.getLogger('cli.harvest.cff')


class CffHarvestSettings(BaseModel):
    """Custom settings for CFF harvester."""
    enable_validation: bool = True


class CffHarvestPlugin(HermesHarvestPlugin):
    settings_class = CffHarvestSettings

    def __call__(self, command: HermesHarvestCommand) -> t.Tuple[t.Dict, t.Dict]:
        # Get source files
        cff_file = self._get_single_cff(command.args.path)
        if not cff_file:
            raise HermesValidationError(f'{command.args.path} contains either no or more than 1 CITATION.cff file. '
                                        'Aborting harvesting for this metadata source.')

        # Read the content
        cff_data = cff_file.read_text()

        # Validate the content to be correct CFF
        cff_dict = self._load_cff_from_file(cff_data)
        if command.settings.cff.enable_validation and not self._validate(cff_file, cff_dict):
            raise HermesValidationError(cff_file)

        # Convert to CodeMeta using cffconvert
        codemeta_dict = self._convert_cff_to_codemeta(cff_data)
        # TODO Replace the following temp patch for #112 once there is a new cffconvert version with cffconvert#309
        codemeta_dict = self._patch_author_emails(cff_dict, codemeta_dict)

        return codemeta_dict, {'local_path': str(cff_file)}

    def _load_cff_from_file(self, cff_data: str) -> t.Any:
        yaml = YAML(typ='safe')
        yaml.constructor.yaml_constructors[u'tag:yaml.org,2002:timestamp'] = yaml.constructor.yaml_constructors[
            u'tag:yaml.org,2002:str']
        return yaml.load(cff_data)

    def _patch_author_emails(self, cff: dict, codemeta: dict) -> dict:
        cff_authors = cff["authors"]
        for i, author in enumerate(cff_authors):
            if "email" in author:
                codemeta["author"][i]["email"] = author["email"]
        return codemeta

    def _convert_cff_to_codemeta(self, cff_data: str) -> t.Any:
        codemeta_str = Citation(cff_data).as_codemeta()
        return json.loads(codemeta_str)

    def _validate(self, cff_file: pathlib.Path, cff_dict: t.Dict) -> bool:
        audit_log = logging.getLogger('audit.cff')

        cff_schema_url = f'https://citation-file-format.github.io/{_CFF_VERSION}/schema.json'

        # TODO: we should ship the schema we reference to by default to avoid unnecessary network traffic.
        #       If the requested version is not already downloaded, go ahead and download it.
        with urllib.request.urlopen(cff_schema_url) as cff_schema_response:
            schema_data = json.loads(cff_schema_response.read())

        validator = jsonschema.Draft7Validator(schema_data)
        errors = sorted(validator.iter_errors(cff_dict), key=lambda e: e.path)
        if len(errors) > 0:
            audit_log.warning('!!! warning "%s is not valid according to <%s>"', cff_file, cff_schema_url)

            for error in errors:
                path = ContextPath.make(error.absolute_path or ['root'])
                audit_log.info('    Invalid input for `%s`.', str(path))
                audit_log.info('    !!! message "%s"', error.message)
                audit_log.debug('    !!! value "%s"', error.instance)

            audit_log.info('')
            audit_log.info('See the Citation File Format schema guide for further details:')
            audit_log.info(
                f'<https://github.com/citation-file-format/citation-file-format/blob/{_CFF_VERSION}/schema-guide.md>.')
            return False

        elif len(errors) == 0:
            audit_log.info('- Found valid Citation File Format file at: %s', cff_file)
            return True

    def _get_single_cff(self, path: pathlib.Path) -> t.Optional[pathlib.Path]:
        # Find CFF files in directories and subdirectories
        cff_file = path / 'CITATION.cff'
        if cff_file.exists():
            return cff_file

        # TODO: Do we really want to search recursive? CFF convention is the file should be at the topmost dir,
        #       which is given via the --path arg. Maybe add another option to enable pointing to a single file?
        #       (So this stays "convention over configuration")
        files = list(path.rglob('**/CITATION.cff'))
        if len(files) == 1:
            return pathlib.Path(files[0])
        # TODO: Shouldn't we log/echo the found CFF files so a user can debug/cleanup?
        # TODO: Do we want to hand down a logging instance via Hermes context or just encourage
        #       peeps to use the Click context?
        return None
