# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>


CODEMETA_PREFIX = "https://doi.org/10.5063/schema/codemeta-2.0"
CODEMETA_CONTEXT = [CODEMETA_PREFIX]

SCHEMA_ORG_PREFIX = "http://schema.org/"
SCHEMA_ORG_CONTEXT = [{"schema": SCHEMA_ORG_PREFIX}]

PROV_PREFIX = "http://www.w3.org/ns/prov#"
PROV_CONTEXT = [{"prov": PROV_PREFIX}]

HERMES_RT_PREFIX = 'https://schema.software-metadata.pub/hermes-runtime/1.0/'
HERMES_RT_CONTEXT = [{'hermes-rt': HERMES_RT_PREFIX}]
HERMES_CONTENT_CONTEXT = [{'hermes': 'https://schema.software-metadata.pub/hermes-content/1.0/'}]

HERMES_CONTEXT = [{**HERMES_RT_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]}]

HERMES_BASE_CONTEXT = [*CODEMETA_CONTEXT, {**SCHEMA_ORG_CONTEXT[0], **HERMES_CONTENT_CONTEXT[0]}]
HERMES_PROV_CONTEXT = [{**SCHEMA_ORG_CONTEXT[0], **HERMES_RT_CONTEXT[0], **PROV_CONTEXT[0]}]

ALL_CONTEXTS = [*CODEMETA_CONTEXT, {**SCHEMA_ORG_CONTEXT[0], **PROV_CONTEXT[0], **HERMES_CONTEXT[0]}]
