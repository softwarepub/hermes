# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json

from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model.path import ContextPath


class FileDepositSettings(BaseModel):
    filename: str = 'hermes.json'


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = FileDepositSettings

    def map_metadata(self) -> None:
        self.ctx.update(ContextPath.parse('deposit.file'), self.ctx['codemeta'])

    def publish(self) -> None:
        file_config = self.command.settings.file
        output_data = self.ctx['deposit.file']

        with open(file_config.filename, 'w') as deposition_file:
            json.dump(output_data, deposition_file, indent=2)
