# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

from importlib import metadata

from hermes.utils import hermes_user_agent

expected_name = "hermes"
expected_homepage = "https://hermes.software-metadata.pub"
dist_version = metadata.version("hermes")


def test_hermes_user_agent():
    assert hermes_user_agent == f"{expected_name}/{dist_version} ({expected_homepage})"
