import click
from importlib import metadata
from hermes.model.context import HermesContext
from hermes.model.errors import HermesValidationError


@click.group(invoke_without_command=True)
def harvest():
    """
    Automatic harvest of metadata
    """
    click.echo("Metadata harvesting")

    ctx = HermesContext()

    # Get all harvesters
    harvesters = metadata.entry_points(group='hermes.harvest')
    for harvester in harvesters:
        harvest = harvester.load()
        try:
            harvest()
        except HermesValidationError as e:
            ctx.error(harvester, e)  # Feed back entry point and errors


@click.group(invoke_without_command=True)
def process():
    """
    Process metadata and prepare it for deposition
    """
    click.echo("Metadata processing")


@click.group(invoke_without_command=True)
def deposit():
    """
    Deposit processed (and curated) metadata
    """
    click.echo("Metadata deposition")


@click.group(invoke_without_command=True)
def post():
    """
    Post-process metadata after deposition
    """
    click.echo("Post-processing")
