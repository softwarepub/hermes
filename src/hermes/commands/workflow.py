import click
from importlib import metadata


@click.group(invoke_without_command=True)
def harvest():
    """
    Automatic harvest of metadata
    """
    click.echo("Metadata harvesting")

    # Get all harvesters
    harvesters = metadata.entry_points(group='hermes.harvest')
    for harvester in harvesters:
        harvest = harvester.load()
        harvest()



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
