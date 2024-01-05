# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel

import json

from hermes import config
from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model.path import ContextPath


class FileDepositPlugin(BaseDepositPlugin):
    def map_metadata(self) -> None:
        self.ctx.update(ContextPath.parse('deposit.file'), self.ctx['codemeta'])

    def publish(self) -> None:
        file_config = config.deposit.get("file", {})
        output_data = self.ctx['deposit.file']

        with open(file_config.get('filename', 'hermes.json'), 'w') as deposition_file:
            json.dump(output_data, deposition_file, indent=2)
