from hermes.model.context import CodeMetaContext, HermesHarvestContext, ContextPath


def flag_authors(ctx: CodeMetaContext, harverst_ctx: HermesHarvestContext):
    data = harverst_ctx.get_data(tags=(tags := {}))

    contributors = []
    author_path = ContextPath('author')

    for i, contributor in enumerate(data.get('author', [])):
        author_key = ctx.find_key(author_path, contributor)
        contributor_key = author_path[i]

        contributor_tags = {}
        for k, t in tags.items():
            if ContextPath.parse(k) in contributor_key:
                subkey = k.lstrip(str(contributor_key) + '.')
                contributor_tags[subkey] = t

        if not author_key:
            contributor['projectRole'] = 'Others'
            contributors.append((contributor, contributor_tags))
        else:
            ctx.update(author_key, contributor, tags=contributor_tags)

    harverst_ctx.finish()

    for author, author_tags in contributors:
        ctx.update(author_path['*'], author, tags=author_tags)
