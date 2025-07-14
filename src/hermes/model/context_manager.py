# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import json
import os.path
import pathlib


class HermesCache:
    def __init__(self, cache_dir: pathlib.Path):
        self._cache_dir = cache_dir
        self._cached_data = {}

    def __enter__(self):
        if self._cache_dir.is_dir():
            for filepath in self._cache_dir.glob('*'):
                basename, _ = os.path.splitext(filepath.name)
                self._cached_data[basename] = json.load(filepath.open('r'))

        return self

    def __getitem__(self, item: str) -> dict:
        if item not in self._cached_data:
            filepath = self._cache_dir / f'{item}.json'
            if filepath.is_file():
                self._cached_data[item] = json.load(filepath.open('r'))

        return self._cached_data[item]

    def __setitem__(self, key: str, value: dict):
        self._cached_data[key] = value

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._cache_dir.mkdir(exist_ok=True, parents=True)

            for basename, data in self._cached_data.items():
                cachefile = self._cache_dir / f'{basename}.json'
                json.dump(data, cachefile.open('w'))


class HermesContext:
    CACHE_DIR_NAME = '.hermes'

    def __init__(self, project_dir: pathlib.Path = pathlib.Path.cwd()):
        self.project_dir = project_dir
        self.cache_dir = project_dir / self.CACHE_DIR_NAME

        self._current_step = []

    def prepare_step(self, step: str, *depends: str) -> None:
        self._current_step.append(step)

    ''' @FIXME #373:

    def finalize_step(self, step: str) -> None:
        current_step = self._current_step[-1]
        if current_step != step:
            raise ValueError(f"Cannot end step {step} while in {self._current_step[-1]}.")
        self._current_step.pop()
    '''
    def finalize_step(self, step: str) -> None:
        current_step = self._current_step.pop()
        if current_step != step:
            raise ValueError("Cannot end step %s while in %s.", step, self._current_step[-1])



    def __getitem__(self, source_name: str) -> HermesCache:
        subdir = self.cache_dir / self._current_step[-1] / source_name
        return HermesCache(subdir)
