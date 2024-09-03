# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import os
import shutil
import subprocess

import pytest


class HermesEnvMock:
    def __init__(self, tmp_path):
        self.hermes_exe = "hermes"
        self.old_path = os.getcwd()
        self.test_path = tmp_path / "hermes_test"
        self.test_files = {}

    def __setitem__(self, path, data):
        self.test_files[path] = data

    def __enter__(self):
        self.test_path.mkdir(parents=True, exist_ok=True)

        for file_name, data in self.test_files.items():
            file_path = self.test_path / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(data)

        os.chdir(self.test_path)

    def run(self, *args):
        proc = subprocess.Popen(
            [self.hermes_exe, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        proc.wait()
        return proc

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_path)
        shutil.rmtree(str(self.test_path))


@pytest.fixture
def hermes_env(tmp_path) -> HermesEnvMock:
    return HermesEnvMock(tmp_path)
