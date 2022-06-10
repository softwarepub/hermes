def harvest_cff(ctx: HermesContext):
    # Get file
    source = cff_source

    # Validate via jsonschema
    try:
        validate()
    except Exception as e:
        raise HermesValidationError('CFF is invalid') from e

    if not valid:
        ctx.error(msg='Sorry, but your CFF is not valid, here are the errors.', errors=errors, src=source)

    # Load
    cff = load(source)

    # Convert
    author = cff.get('authors')

    ctx.update('author', author, src=source)
    print('Hello CFF harvester')