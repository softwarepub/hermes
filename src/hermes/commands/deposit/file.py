# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json

from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model import SoftwareMetadata

class FileDepositSettings(BaseModel):
    filename: str = 'codemeta.json'


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = FileDepositSettings

    def map_metadata(self) -> SoftwareMetadata:
        return self.metadata

    def publish(self) -> None:
        file_config = self.command.settings.file

        with open(file_config.filename, 'w') as deposition_file:
            json.dump(self.metadata.compact(), deposition_file, indent=2)
