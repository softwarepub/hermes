import argparse

from hermes.commands.base import HermesCommand


class HermesCurateCommand(HermesCommand):
    """ Curate the unified metadata before deposition. """

    command_name = "curate"

    def __call__(self, args: argparse.Namespace) -> None:
        pass
