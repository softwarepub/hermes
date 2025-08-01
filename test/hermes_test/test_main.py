# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

# flake8: noqa

import pytest

pytest.skip("FIXME: Re-enable test after data model refactoring is done.", allow_module_level=True)

import subprocess
import sys


def test_hermes_command():
    assert subprocess.check_call([sys.executable, "-m", "hermes", "--help"]) == 0


def test_hermes_import():
    from hermes import __main__

    assert __main__.__name__ != '__main__'
