# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import logging

from hermes.model.context import CodeMetaContext, HermesHarvestContext, ContextPath


_AUTHOR_KEYS = ('@id', 'email', 'name')


def flag_authors(ctx: CodeMetaContext, harverst_ctx: HermesHarvestContext):
    """
    Add all git authors and committers with role `Contributor`.

    :param ctx: The target context containting harmonized data.
    :param harverst_ctx: Data as it was harvested.
    """
    audit_log = logging.getLogger('audit.git')
    audit_log.info('')
    audit_log.info('### Add git authors and committers as contributors')

    author_path = ContextPath('author')
    contributor_path = ContextPath('contributor')

    tags = {}
    try:
        data = harverst_ctx.get_data(tags=tags)
    except ValueError:
        audit_log.info("- Inconsistent data, skipping.")
        return

    for i, contributor in enumerate(author_path.get_from(data)):
        audit_log.debug('- %s', contributor['name'])
        if contributor_path not in ctx.keys():
            ctx.update(contributor_path, [])
        ctx.update(contributor_path['*'], contributor, tags=tags)

    ctx.tags.update(tags)
    harverst_ctx.finish()
