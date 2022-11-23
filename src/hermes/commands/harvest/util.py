import pathlib

import click


def get_project_path(click_ctx: click.Context) -> pathlib.PosixPath:
    """Returns the 'path' parameter of the passed click.Context's parent context.
    Every subcommand has its own click context with the main click context as parent.

    :param click_ctx: The subcommand's click context
    :return: The path parameter of the passed click.Context's parent path, i.e.,
    the path where the workflow CLI tool was executed, i.e.,
    the root path of the project that the workflow tool is run for.
    """
    parent_ctx = click_ctx.parent
    if parent_ctx is None:
        raise RuntimeError('No parent context!')
    return parent_ctx.params['path']
