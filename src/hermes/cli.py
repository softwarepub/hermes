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


def main(*args, **kwargs) -> None:
    """
    HERMES

    This command runs the HERMES workflow or parts of it.
    """
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="This command runs the HERMES workflow or parts of it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default=pathlib.Path("hermes.toml"),
        help="Configuration file in TOML format",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--curate",
        action="store_true",
        default=False,
        help="Run the 'curate' workflow step",
    )
    parser.add_argument(
        "--deposit",
        action="store_true",
        default=False,
        help="Run the 'deposit' workflow step",
    )
    parser.add_argument(
        "--postprocess",
        action="store_true",
        default=False,
        help="Run the 'postprocess' workflow step",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Remove cached data",
    )
    parser.add_argument(
        "--path", default=pathlib.Path("./"), help="Working path", type=pathlib.Path
    )
    args = parser.parse_args()
