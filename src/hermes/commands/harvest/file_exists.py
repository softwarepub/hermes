# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

from dataclasses import dataclass
from functools import cache
from mimetypes import guess_type
from pathlib import Path
from typing import List, Optional
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

    @classmethod
    def from_path(cls, path: Path) -> Self:
        text_object = TextObject.from_path(path)
        return cls(name=path.stem, associated_media=text_object)

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:CreativeWork",
            "schema:name": self.name,
            "schema:associatedMedia": self.associated_media.as_codemeta(),
        }


class FileExistsHarvestSettings(BaseModel):
    """Settings for ``file_exists`` harvester."""

    enable_git_ls_files: bool = True


class FileExistsHarvestPlugin(HermesHarvestPlugin):
    settings_class = FileExistsHarvestSettings

    search_patterns = [
        "contributing",
        "contributing.md",
        "contributing.txt",
    ]
    search_patterns_license = [
        "license",
        "license.txt",
        "license.md",
        "licenses/*.txt",
    ]
    search_patterns_readme = [
        "readme",
        "readme.md",
        "readme.markdown",
        "readme.rst",
        "readme.txt",
    ]

    def __init__(self):
        self.working_directory: Path = Path.cwd()
        self.settings: FileExistsHarvestSettings = FileExistsHarvestSettings()

    def __call__(self, command: HermesHarvestCommand):
        self.working_directory = command.args.path.resolve()
        self.settings = command.settings.file_exists

        license_files = self._find_files(self.search_patterns_license)
        readme_files = self._find_files(self.search_patterns_readme)
        other_files = self._find_files(self.search_patterns)

        data = {
            "schema:hasPart": [
                file.as_codemeta()
                for file in license_files + readme_files + other_files
            ],
            "schema:license": [
                file.associated_media.url.as_codemeta() for file in license_files
            ],
            "codemeta:readme": [
                file.associated_media.url.as_codemeta() for file in readme_files
            ],
        }

        return data, {"workingDirectory": str(self.working_directory)}

    def _find_files(self, file_name_patterns: List[str]) -> List[CreativeWork]:
        """Find files that match ``file_name_patterns``.

        If the setting ``enable_git_ls_files`` is ``True``, ``git ls-files`` is used to
        find matching files. If it is set to ``False`` or getting the list from git
        fails, the working directory is searched recursively.
        """
        files = None
        if self.settings.enable_git_ls_files:
            files = self._find_files_git(file_name_patterns)
        if files is None:
            files = self._find_files_directory(file_name_patterns)
        return [CreativeWork.from_path(file) for file in files]

    def _find_files_directory(self, file_name_patterns: List[str]) -> List[Path]:
        results = set()
        for pattern in file_name_patterns:
            paths = self.working_directory.rglob(pattern, case_sensitive=False)
            results.update(paths)
        return list(results)

    def _find_files_git(self, file_name_patterns: List[str]) -> Optional[List[Path]]:
        files = _git_ls_files(self.working_directory)
        if files is None:
            return None
        matching_files = []
        for file in files:
            for pattern in file_name_patterns:
                if file.match(pattern, case_sensitive=False):
                    matching_files.append(file)
        return matching_files


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
