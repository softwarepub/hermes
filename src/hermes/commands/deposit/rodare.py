# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from hermes.commands.deposit.invenio import InvenioDepositPlugin

class RodareDepositPlugin(InvenioDepositPlugin):
    platform_name = "rodare"
