# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import logging

from hermes.model.context import HermesHarvestContext, ContextPath, CodeMetaContext


def add_name(ctx: CodeMetaContext, harvest_ctx: HermesHarvestContext):
    """
    Augment each author with a `name` attribute (if not present).

    This will allow better matching against the git authors and can be removed in a post-processing step.

    :param ctx: The resulting context that should contain the harmonized data.
    :param harvest_ctx: The harvest context containing all raw harvested data.
    """
    audit_log = logging.getLogger('audit.cff')
    audit_log.info('')
    audit_log.info('### Add author names')

    data = harvest_ctx.get_data()
    author_path = ContextPath('author')

    for i, author in enumerate(data.get('author', [])):
        if 'name' not in author:
            harvest_ctx.update(str(author_path[i]["name"]), f"{author['givenName']} {author['familyName']}",
                               stage='preprocess')
            audit_log.debug(f"- {author['givenName']} {author['familyName']}")
