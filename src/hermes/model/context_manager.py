# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import json
import os.path
from pathlib import Path
from types import TracebackType
from typing import Union
from typing_extensions import Self

from .error import HermesContextError


class HermesCache:
    """
    The HermesCache supplies the user with easy (read and write) access to the JSON files in the cache.

    Attributes:
        _cache_dir (Path): The directory the cache is located at.
        _cached_data (dict[str, dict]): The cache of the files in the cache. The key is the filename.
    """
    def __init__(self: Self, cache_dir: Path) -> None:
        """
        Creates a new HermesCache instance.

        Args:
            cache_dir (Path): The directory the files are located in.

        Returns:
            None:
        """
        self._cache_dir = cache_dir
        self._cached_data = {}

    def __enter__(self: Self) -> None:
        """
        Caches all files in the cache_dir.

        Returns:
            None:
        """
        if self._cache_dir.is_dir():
            for filepath in self._cache_dir.glob('*'):
                basename, _ = os.path.splitext(filepath.name)
                self._cached_data[basename] = json.load(filepath.open('r'))

        return self

    def __getitem__(self: Self, item: str) -> dict:
        """
        Loads a file if necessary or returns the cached value.

        Args:
            item (str): The name of the file.

        Returns:
            dict: The JSON value in the given file.
        """
        if item not in self._cached_data:
            filepath = self._cache_dir / f'{item}.json'
            if filepath.is_file():
                self._cached_data[item] = json.load(filepath.open('r'))

        return self._cached_data[item]

    def __setitem__(self: Self, key: str, value: dict) -> None:
        """
        Writes a value into the cache.\n
        Note that the files isn't immediately updated only the cache is.

        Args:
            key (str): The filename the data is written too.
            value (dict): The JSON value for the file.

        Returns:
            None:
        """
        self._cached_data[key] = value

    def __exit__(
        self: Self,
        exc_type: Union[type[BaseException], None],
        exc_val: Union[BaseException, None],
        exc_tb: Union[TracebackType, None]
    ) -> None:
        """
        Updates the files from the cache.

        Args:
            exc_type (type[BaseException] | None): The type of the exception.
            exc_val: (BaseException | None): Unused
            exc_tb: (TracebackType | None): Unused

        Returns:
            None:
        """
        if exc_type is None:
            self._cache_dir.mkdir(exist_ok=True, parents=True)

            for basename, data in self._cached_data.items():
                cachefile = self._cache_dir / f'{basename}.json'
                json.dump(data, cachefile.open('w'))


class HermesContext:
    """
    The HermesContext supplies the user with easy access to the HERMES cache.

    Attributes:
        project_dir (Path): The directory the project is located in.
        cache_dir (Path): The cache directory inside the project_dir.
        _current_step (list[str]): The list of steps (i.e. cache names).
        CACHE_DIR_NAME (str): (class attribute) The relative directory all HERMES caches are located in.
    """
    CACHE_DIR_NAME = '.hermes'

    def __init__(self: Self, project_dir: Path = Path.cwd()) -> None:
        """
        Creates a new instance of the HermesContext.

        Args:
            project_dir (Path): The directory the project is located in.

        Returns:
            None:
        """
        self.project_dir = project_dir
        self.cache_dir = project_dir / self.CACHE_DIR_NAME

        self._current_step = []

    def prepare_step(self: Self, step: str) -> None:
        """
        Add another cache dir to the list of steps.

        Args:
            step (str): The new cache dir.

        Returns:
            None:
        """
        self._current_step.append(step)

    def finalize_step(self: Self, step: str) -> None:
        """
        Remove the step from the list of steps if it is the last one.

        Args:
            step (str): The cache dir that is removed.

        Returns:
            None:

        Raises:
            ValueError: If no step can be removed.
            ValueError: If the given step is not the last one.
        """
        if len(self._current_step) < 1:
            raise ValueError("There is no step to end.")
        if self._current_step[-1] != step:
            raise ValueError(f"Cannot end step {step} while in {self._current_step[-1]}.")
        self._current_step.pop()

    def __getitem__(self: Self, source_name: str) -> HermesCache:
        """
        Return the HERMES cache at the current cache dir and the given sub dir (source_name).

        Args:
            source_name (str): The name of the sub dir of the current cache dir.

        Returns:
            HermesCache: The HermesCache object of the cache.

        Raises:
            HermesContextError: If no step has been prepared (i.e. no current cache dir is set).
        """
        if len(self._current_step) < 1:
            raise HermesContextError("Prepare a step first.")
        subdir = self.cache_dir / self._current_step[-1] / source_name
        return HermesCache(subdir)
