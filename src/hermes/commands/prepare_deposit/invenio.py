# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import requests

from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def prepare_invenio_deposit(ctx: CodeMetaContext):
    """Prepare the Invenio deposit.

    In this case, "prepare" means download the record schema that is required
    by Invenio instances. This is the basis that will be used for metadata
    mapping in the next step.
    """

    invenio_path = ContextPath.parse("deposit.invenio")

    invenio_ctx = ctx[invenio_path]
    recordSchemaUrl = f"{invenio_ctx['siteUrl']}/{invenio_ctx['recordSchemaPath']}"

    recordSchema = _request_json(recordSchemaUrl)
    ctx.update(invenio_path["requiredSchema"], recordSchema)


def _request_json(url: str):
    """Request an URL and return the response as JSON."""

    # TODO: Store a requests.Session in a click_ctx in case we need it more frequently?
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
