# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

import toml

from importlib.resources import files

pyproject = toml.loads(files("hermes").joinpath("../../pyproject.toml").read_text())
expected_name = pyproject["project"]["name"]
expected_version = pyproject["project"]["version"]
expected_homepage = pyproject["project"]["urls"]["homepage"]


def test_hermes_user_agent():
    """
    This assumes that no other version of `hermes` than the current one is installed
    in the workspace from which the tests are run.
    """
    from hermes.utils import hermes_user_agent
    assert (
        hermes_user_agent == f"{expected_name}/{expected_version} ({expected_homepage})"
    )
