# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json
import logging
import os

from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin


_log = logging.getLogger("cli.deposit.file")


class FileDepositSettings(BaseModel):
    filename: str = 'hermes.json'


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = FileDepositSettings

    def map_metadata(self) -> dict:
        return self.metadata.compact()

    def update_metadata(self) -> dict:
        return self.metadata.compact()

    def publish(self) -> None:
        file_config = self.command.settings.file

        with open(file_config.filename, 'w') as deposition_file:
            json.dump(self.metadata.compact(), deposition_file, indent=2)
        _log.info(f"The deposited metadata can be found in {os.path.abspath(file_config.filename)}.")
