# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import requests

from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


def prepare_invenio(ctx: CodeMetaContext):
    _get_invenio_requirements(f"{INVENIO_SITE_URL}/{INVENIO_RECORD_SCHEMA_PATH}")


def _get_invenio_requirements(url):
    # TODO: requests.Session in context?
    response = requests.get(url)
    print(response.json())