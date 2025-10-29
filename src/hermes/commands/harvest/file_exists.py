# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from mimetypes import guess_type
from pathlib import Path
from typing import Dict, List, Optional, Set
from typing_extensions import Self
import subprocess

from pydantic import BaseModel

from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin


@dataclass
class URL:
    url: str

    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(url=path.as_uri())

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:URL",
            "@value": self.url,
        }


@dataclass
class TextObject:
    content_size: str
    encoding_format: str
    url: URL

    @classmethod
    def from_path(cls, path: Path) -> Self:
        size = str(path.stat().st_size)  # string!
        type_, _encoding = guess_type(path)
        url = URL.from_path(path)
        return cls(content_size=size, encoding_format=type_, url=url)

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:TextObject",
            "schema:contentSize": self.content_size,
            "schema:encodingFormat": self.encoding_format,
            "schema:url": self.url.as_codemeta(),
        }


@dataclass
class CreativeWork:
    name: str
    associated_media: TextObject
    keywords: List[str]

    @classmethod
    def from_path(cls, path: Path, keywords: List[str]) -> Self:
        text_object = TextObject.from_path(path)
        return cls(name=path.stem, associated_media=text_object, keywords=keywords)

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:CreativeWork",
            "schema:name": self.name,
            "schema:associatedMedia": self.associated_media.as_codemeta(),
            "schema:keywords": self.keywords,
        }


class FileExistsHarvestSettings(BaseModel):
    """Settings for ``file_exists`` harvester."""

    enable_git_ls_files: bool = True
    search_patterns: Dict[str, List[str]] = {}


class FileExistsHarvestPlugin(HermesHarvestPlugin):
    settings_class = FileExistsHarvestSettings

    base_search_patterns = {
        "readme": [
            "readme",
            "readme.md",
            "readme.markdown",
            "readme.rst",
            "readme.txt",
        ],
        "license": [
            "license",
            "license.txt",
            "license.md",
            "licenses/*.txt",
        ],
    }

    def __init__(self):
        self.working_directory: Path = Path.cwd()
        self.settings: FileExistsHarvestSettings = FileExistsHarvestSettings()

        # mapping from tag name to list of file name patterns
        self.search_patterns: Dict[str, List[str]] = self.base_search_patterns
        # mapping from file name pattern to list of tags
        self.search_pattern_keywords: Dict[str, List[str]] = defaultdict(list)
        # flat list of file name patterns
        self.search_pattern_list: List[str] = []

    def __call__(self, command: HermesHarvestCommand):
        self.working_directory = command.args.path.resolve()
        self.settings = command.settings.file_exists

        # update search patterns from config
        self.search_patterns.update(self.settings.search_patterns)

        # create inverse lookup table
        for key, patterns in self.search_patterns.items():
            for pattern in patterns:
                self.search_pattern_keywords[pattern].append(key)

        self.search_pattern_list = sum(self.search_patterns.values(), start=[])

        files = self._find_files()
        data = {
            "schema:hasPart": [file.as_codemeta() for file in files],
            "schema:license": [
                file.associated_media.url.as_codemeta()
                for file in files
                if file.keywords and "license" in file.keywords
            ],
            "codemeta:readme": [
                file.associated_media.url.as_codemeta()
                for file in files
                if file.keywords and "readme" in file.keywords
            ],
        }

        return data, {"workingDirectory": str(self.working_directory)}

    def _find_files(self) -> List[CreativeWork]:
        """Find files that match the search patterns.

        If the setting ``enable_git_ls_files`` is ``True``, ``git ls-files`` is used to
        find matching files. If it is set to ``False`` or getting the list from git
        fails, the working directory is searched recursively.

        The files are tagged using the search pattern "groups" as the keywords.
        """
        files = None
        if self.settings.enable_git_ls_files:
            files = _git_ls_files(self.working_directory)
        if files is None:
            files = self.working_directory.rglob("*")
        files_with_keywords = self._tag_files(files)
        return [
            CreativeWork.from_path(file, keywords=list(keywords))
            for file, keywords in files_with_keywords.items()
        ]

    def _tag_files(self, paths: List[Path]) -> Optional[Dict[Path, Set[str]]]:
        """Filter and tag file paths."""
        paths_with_keywords = defaultdict(set)
        for path in paths:
            for pattern in self.search_pattern_list:
                if path.match(pattern, case_sensitive=False):
                    keywords = self.search_pattern_keywords[pattern]
                    paths_with_keywords[path].update(keywords)
        return paths_with_keywords


@cache
def _git_ls_files(working_directory: Path) -> Optional[List[Path]]:
    """Get a list of all files by calling ``git ls-file`` in ``working_directory``.

    ``git ls-file`` is called with the ``--cached`` flag which lists all files tracked
    by git. The returned file paths are converted to a list of ``Path`` objects. If the
    git command fails or git is not found, ``None`` is returned.

    The result of this function is cached. Git is only executed once per given
    ``working_directory``.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached"],
            capture_output=True,
            cwd=working_directory,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    filenames = result.stdout.splitlines()
    files = [Path(filename).resolve() for filename in filenames]
    return files
