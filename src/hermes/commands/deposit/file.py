# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json

from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin


class FileDepositSettings(BaseModel):
    filename: str = 'codemeta.json'


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = FileDepositSettings

    def publish(self) -> None:
        file_config = self.command.settings.file

        with open(file_config.filename, 'w') as deposition_file:
            json.dump(self.metadata.compact(), deposition_file, indent=2)
