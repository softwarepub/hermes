from hermes.model.context import HermesHarvestContext, ContextPath, CodeMetaContext


def add_name(ctx: CodeMetaContext, harvest_ctx: HermesHarvestContext):
    data = harvest_ctx.get_data()
    author_path = ContextPath('author')

    for i, author in enumerate(data.get('author', [])):
        if 'name' not in author:
            harvest_ctx.update(str(author_path[i]["name"]), f"{author['givenName']} {author['familyName']}", stage='preprocess')
