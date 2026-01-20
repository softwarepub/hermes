# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

import glob
import json
import pathlib
import typing as t

from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin
from hermes.commands.harvest.util.validate_codemeta import validate_codemeta
from hermes.model.errors import HermesValidationError
from hermes.commands.harvest.util.remote_harvesting import normalize_url, fetch_metadata_from_repo
from hermes.commands.harvest.util.token import load_token_from_toml

class CodeMetaHarvestPlugin(HermesHarvestPlugin):
    def __call__(self, command: HermesHarvestCommand) -> t.Tuple[t.Dict, t.Dict]:
        
        self.token = load_token_from_toml('hermes.toml')
        
        """
        Implementation of a harvester that provides data from a codemeta.json file format.

        :param path: The working path
        :param config_path: The path to the config TOML file
        :param ctx: The harvesting context that should contain the provided metadata.
        """
        # Get source files
        codemeta_file, temp_dir_obj = self._get_single_codemeta(command.args.path)
        if not codemeta_file:
            raise HermesValidationError(
                f"{command.args.path} contains either no or more than 1 codemeta.json file. Aborting harvesting "
                f"for this metadata source."
            )

        # Read the content
        codemeta_str = codemeta_file.read_text(encoding='utf-8')

        if not self._validate(codemeta_file):
            raise HermesValidationError(codemeta_file)

        if temp_dir_obj:
            temp_dir_obj.cleanup()

        codemeta = json.loads(codemeta_str)
        return codemeta, {'local_path': str(codemeta_file)}

    def _validate(self, codemeta_file: pathlib.Path) -> bool:
        with open(codemeta_file, "r") as fi:
            try:
                codemeta_json = json.load(fi)
            except json.decoder.JSONDecodeError as jde:
                raise HermesValidationError(
                    f"CodeMeta file at {codemeta_file} cannot be decoded into JSON.", jde
                )

        if not validate_codemeta(codemeta_json):
            raise HermesValidationError("Validation of CodeMeta file failed.")

        return True

    def _get_single_codemeta(self, path: pathlib.Path) -> t.Optional[pathlib.Path]:
        if str(path).startswith("http:") or str(path).startswith("https:"):
            # Find CodeMeta files from the provided URL repository
            normalized_url = normalize_url(str(path))
            file_info = fetch_metadata_from_repo(normalized_url, "codemeta.json", token=self.token)
            if not file_info:
                return None, None 
            else:
                return file_info
        else:
            # Find CodeMeta files in directories and subdirectories
            # TODO: Do we really want to search recursive? Maybe add another option to enable pointing to a single file?
            #       (So this stays "convention over configuration")
            files = glob.glob(str(path / "**" / "codemeta.json"), recursive=True)
            if len(files) == 1:
                return pathlib.Path(files[0]), None
            # TODO: Shouldn't we log/echo the found CFF files so a user can debug/cleanup?
            # TODO: Do we want to hand down a logging instance via Hermes context or just encourage
            #       peeps to use the Click context?
            return None, None