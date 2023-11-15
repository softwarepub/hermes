# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Druskat
# SPDX-FileContributor: Michael Meinel

"""
This module provides the main entry point for the HERMES command line application.
"""
import pathlib
import argparse
import sys

from hermes.commands.workflow import (
    clean,
    harvest,
    process,
    curate,
    deposit,
    postprocess,
)


def main(*args, **kwargs) -> None:
    """
    HERMES

    This command runs the HERMES workflow or parts of it.
    """
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="This command runs HERMES workflow steps.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Arguments
    parser.add_argument(
        "--path", default=pathlib.Path("./"), help="Working path", type=pathlib.Path
    )
    parser.add_argument(
        "--config",
        default=pathlib.Path("hermes.toml"),
        help="Configuration file in TOML format",
        type=pathlib.Path,
    )

    subparsers = parser.add_subparsers(help="Available subcommands", required=True)

    # Subcommand clean
    parser_clean = subparsers.add_parser("clean", help="Removes cached data")
    parser_clean.set_defaults(func=clean)

    # Subcommand harvest
    parser_harvest = subparsers.add_parser(
        "harvest", help="Harvest metadata from configured sources"
    )
    parser_harvest.set_defaults(func=harvest)

    # Subcommand process
    parser_process = subparsers.add_parser(
        "process", help="Process the harvested metadata into a unified model"
    )
    parser_process.set_defaults(func=process)

    # Subcommand curate
    parser_curate = subparsers.add_parser(
        "curate",
        help="Resolve issues and conflicts in the processed metadata to create a curated set of metadata",
    )
    parser_curate.set_defaults(func=curate)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    args.func(args)

    # main.add_command(workflow.curate)
    # main.add_command(workflow.deposit)
    # main.add_command(workflow.postprocess)
