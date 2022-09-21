from hermes.model.context import CodeMetaContext, HermesHarvestContext, ContextPath


_AUTHOR_KEYS = ('@id', 'email', 'name')


def flag_authors(ctx: CodeMetaContext, harverst_ctx: HermesHarvestContext):
    tags = {}
    data = harverst_ctx.get_data(tags=tags)
    author_path = ContextPath('author')

    for i, contributor in enumerate(author_path.get_from(data)):
        query = {k: contributor[k] for k in _AUTHOR_KEYS if k in contributor}
        author_key, target, path = author_path['*'].resolve(ctx._data, query=query)

        if author_key._item == '*':
            contributor['projectRole'] = 'Others'

        ctx.update(author_key, contributor, tags=tags)

    ctx.tags.update(tags)
    harverst_ctx.finish()
