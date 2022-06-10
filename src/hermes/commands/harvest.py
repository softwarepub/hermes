from pathlib import Path

from hermes.model.context import HermesContext
from hermes.model.errors import HermesValidationError


def harvest_cff(ctx: HermesContext):
    # Get file
    source = get_cff()

    # Validate via jsonschema
    try:
        validate()
    except Exception as e:
        raise HermesValidationError(f'{source} is invalid') from e

    # Load
    cff = read_cff(source)

    # Convert
    author = cff.get('authors')

    ctx.update('author', author, src=source)
    print('Hello CFF harvester')


def read_cff():
    return {}


def validate():
    pass


def get_cff():
    return Path
