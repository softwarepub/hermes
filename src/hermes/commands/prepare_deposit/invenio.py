# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import requests

from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def prepare_invenio(ctx: CodeMetaContext):
    invenio_path = ContextPath.parse("deposit.invenio")

    invenio_ctx = ctx[invenio_path]
    recordSchemaUrl = f"{invenio_ctx['siteUrl']}/{invenio_ctx['recordSchemaPath']}"

    recordSchema = _get_invenio_record_schema(recordSchemaUrl)
    ctx.update(invenio_path["requiredSchema"], recordSchema)


def _get_invenio_record_schema(url):
    # TODO: Store a requests.Session in a click_ctx in case we need it more frequently?
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
