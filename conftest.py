# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

# add option to pass zenodo sandbox auth token to pytest to run ./test/hermes_test/commands/deposit/test_invenio_e2e.py
def pytest_addoption(parser):
    parser.addoption("--sandbox_auth", action="store", default=None)
