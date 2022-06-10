def harvest_cff(ctx: HermesContext):
    # Get file
    source = cff_source

    # Validate

    # Load
    cff = load(source)

    # Convert
    author = cff.get('authors')

    ctx.update('author', author, src=source)
    print('Hello CFF harvester')