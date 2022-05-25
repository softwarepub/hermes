import click


@click.group(invoke_without_command=True)
def harvest():
    """
    Automatic harvest of metadata
    """
    click.echo("Metadata harvesting")


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
