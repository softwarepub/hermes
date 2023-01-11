import logging

from hermes.model.context import CodeMetaContext, HermesHarvestContext, ContextPath


_AUTHOR_KEYS = ('@id', 'email', 'name')


def flag_authors(ctx: CodeMetaContext, harverst_ctx: HermesHarvestContext):
    """
    Identify all authors that are not yet in the target context and flag them with role `Contributor`.

    :param ctx: The target context containting harmonized data.
    :param harverst_ctx: Data as it was harvested.
    """
    audit_log = logging.getLogger('audit.git')
    audit_log.info('')
    audit_log.info('### Flag new authors')

    author_path = ContextPath('author')
    tags = {}
    try:
        data = harverst_ctx.get_data(tags=tags)
    except ValueError:
        audit_log.info("- Inconsistent data, skipping.")
        return

    for i, contributor in enumerate(author_path.get_from(data)):
        query = {k: contributor[k] for k in _AUTHOR_KEYS if k in contributor}
        author_key, target, path = author_path['*'].resolve(ctx._data, query=query)

        if author_key._item == '*':
            contributor['projectRole'] = 'Contributor'
            audit_log.debug('- %s', contributor['name'])

        ctx.update(author_key, contributor, tags=tags)

    ctx.tags.update(tags)
    harverst_ctx.finish()
