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
import os
from os import access, R_OK

from hermes.commands.workflow import (
    clean,
    harvest,
    process,
    curate,
    deposit,
    postprocess,
)


def _is_valid_file(parser, f):
    p = pathlib.Path(f)
    if not p.exists():
        parser.error(f"The file {f} does not exist!")
    if p.is_dir():
        parser.error(f"{f} is a directory, not a file!")
    if not access(f, R_OK):
        parser.error(f"The file {f} is not readable!")
    return pathlib.Path(f)


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

    subparsers = parser.add_subparsers(
        help="Available subcommands", required=True, dest="subcommand"
    )

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

    # Subcommand deposit
    parser_deposit = subparsers.add_parser(
        "deposit",
        help="Deposit the curated metadata and any artifacts in the configured target(s)",
    )
    parser_deposit.set_defaults(func=deposit)
    parser_deposit.add_argument(
        "--initial",
        action="store_false",
        default=False,
        help="Allow initial deposition if no previous version exists in target repository. "
        "Otherwise only an existing, configured upstream record may be updated.",
    )
    parser_deposit.add_argument(
        "--auth-token",
        default=os.environ.get("HERMES_DEPOSITION_AUTH_TOKEN"),
        help="Token used to authenticate the user with the target deposition platform; "
        "can be passed on the command line or set in an environment variable 'HERMES_DEPOSITION_AUTH_TOKEN'",
    )
    parser_deposit.add_argument(
        "--files",
        "-f",
        required=True,
        type=lambda f: _is_valid_file(parser, f),
        nargs="+",
        help="Files to be uploaded on the target deposition platform",
    )

    # Subcommand curate
    parser_postprocess = subparsers.add_parser(
        "postprocess",
        help="Postprocess the deposited metadata",
    )
    parser_postprocess.set_defaults(func=postprocess)

    # Show the help string if no arguments are given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Call the configured function of the argument
    if args.subcommand == "deposit":
        args.func(args.path, args.config, args.initial, args.auth_token, args.files)
    else:
        args.func(args.path, args.config)
