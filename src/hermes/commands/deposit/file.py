# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR), Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json

from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.model.types import ld_list, ld_dict, ld_context


class FileDepositSettings(BaseModel):
    filename: str = 'codemeta.json'
    include_prov: bool = False


class FileDepositPlugin(BaseDepositPlugin):
    settings_class = FileDepositSettings

    def map_metadata(self) -> None:
        if not self.command.settings.file.include_prov:
            self._strip_namespace(self.ctx, ld_context.HERMES_RT_PREFIX)

    def _strip_namespace(self, ctx, ns):
        if isinstance(ctx, ld_dict):
            for key, value in [*ctx.items()]:
                if key.startswith(ns):
                    del ctx[key]
                else:
                    self._strip_namespace(value, ns)
        elif isinstance(ctx, ld_list):
            for item in ctx:
                self._strip_namespace(item, ns)

    def publish(self) -> None:
        file_config = self.command.settings.file

        with open(file_config.filename, 'w') as deposition_file:
            json.dump(self.ctx.compact(), deposition_file, indent=2)
