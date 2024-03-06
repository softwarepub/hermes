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


class CodeMetaHarvestPlugin(HermesHarvestPlugin):
    def __call__(self, command: HermesHarvestCommand) -> t.Tuple[t.Dict, t.Dict]:
        """
        Implementation of a harvester that provides data from a codemeta.json file format.

        :param path: The working path
        :param config_path: The path to the config TOML file
        :param ctx: The harvesting context that should contain the provided metadata.
        """
        # Get source files
        codemeta_file = self._get_single_codemeta(command.args.path)
        if not codemeta_file:
            raise HermesValidationError(
                f"{command.args.path} contains either no or more than 1 codemeta.json file. Aborting harvesting "
                f"for this metadata source."
            )

        # Read the content
        codemeta_str = codemeta_file.read_text()

        if not self._validate(codemeta_file):
            raise HermesValidationError(codemeta_file)

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
        # Find CodeMeta files in directories and subdirectories
        # TODO: Do we really want to search recursive? Maybe add another option to enable pointing to a single file?
        #       (So this stays "convention over configuration")
        files = glob.glob(str(path / "**" / "codemeta.json"), recursive=True)
        if len(files) == 1:
            return pathlib.Path(files[0])
        # TODO: Shouldn't we log/echo the found CFF files so a user can debug/cleanup?
        # TODO: Do we want to hand down a logging instance via Hermes context or just encourage
        #       peeps to use the Click context?
        return None
