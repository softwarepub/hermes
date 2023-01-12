# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import click
import requests

from hermes.model.context import HermesContext

INVENIO_SITE_URL = "https://zenodo.org"
INVENIO_RECORD_SCHEMA_PATH = "api/schemas/records/record-v1.0.0.json"

# TODO: HermesDepositContext?
def prepare_invenio(click_ctx: click.Context, ctx: HermesContext):
    _get_invenio_requirements()


def _get_invenio_requirements():
    # TODO: requests.Session in context?
    response = requests.get(f"{INVENIO_SITE_URL}/{INVENIO_RECORD_SCHEMA_PATH}")
    print(response.json())