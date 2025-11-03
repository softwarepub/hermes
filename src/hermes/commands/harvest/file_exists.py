# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

"""Module for the ``FileExistsHarvestPlugin`` and it's associated models and helpers."""

from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from mimetypes import guess_type
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
from typing_extensions import Self
import subprocess

from pydantic import BaseModel

from hermes.commands.harvest.base import HermesHarvestCommand, HermesHarvestPlugin


def guess_file_type(path: Path):
    """File type detection for non-standardised formats.

    Custom detection for file types not yet supported by Python's ``guess_type``
    function.
    """
    # YAML was only added to ``guess_type`` in Python 3.14 due to the MIME type only
    # having been decided in 2024.
    # See: https://www.rfc-editor.org/rfc/rfc9512.html
    if path.suffix in [".yml", ".yaml"]:
        return ("application/yaml", None)

    # TOML is not yet part of ``guess_type`` due to the MIME type only having been
    # accepted in October of 2024.
    # See: https://www.iana.org/assignments/media-types/application/toml
    if path.suffix == ".toml":
        return ("application/toml", None)

    # cff is yaml.
    # See: https://github.com/citation-file-format/citation-file-format/issues/391
    if path.name == "CITATION.cff":
        return ("application/yaml", None)

    # .license files are likely license annotations according to REUSE specification.
    # See: https://reuse.software/spec/
    if path.suffix == ".license":
        return ("text/plain", None)

    if path.name == "poetry.lock":
        return ("text/plain", None)

    # use non-strict mode to cover more file types
    return guess_type(path, strict=False)


@dataclass
class URL:
    """Basic model of a ``schema:URL``.

    See also: https://schema.org/URL
    """

    url: str

    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls(url=path.as_uri())

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:URL",
            "@value": self.url,
        }


# TODO: Support other common subtypes of ``MediaObject`` such as ``ImageObject``.
# Currently, these are incorrectly classified as ``TextObject``.
@dataclass
class TextObject:
    """Basic model of a ``schema:TextObject``.

    See also: https://schema.org/TextObject
    """

    content_size: str
    encoding_format: Optional[str]
    url: URL

    @classmethod
    def from_path(cls, path: Path) -> Self:
        size = str(path.stat().st_size)  # string!
        type_, _encoding = guess_file_type(path)
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
    """Basic model of a ``schema:CreativeWork``.

    See also: https://schema.org/CreativeWork
    """

    name: str
    associated_media: TextObject
    keywords: Set[str]

    @classmethod
    def from_path(cls, path: Path, keywords: Set[str]) -> Self:
        text_object = TextObject.from_path(path)
        return cls(name=path.stem, associated_media=text_object, keywords=set(keywords))

    def as_codemeta(self) -> dict:
        return {
            "@type": "schema:CreativeWork",
            "schema:name": self.name,
            "schema:associatedMedia": self.associated_media.as_codemeta(),
            "schema:keywords": list(self.keywords),
        }


class FileExistsHarvestSettings(BaseModel):
    """Settings for ``file_exists`` harvester."""

    enable_git_ls_files: bool = True
    search_patterns: Dict[str, List[str]] = {}


class FileExistsHarvestPlugin(HermesHarvestPlugin):
    """Harvest plugin that searches for specific files based on patterns.

    Files are searched based on patterns such as ``readme.md`` or ``licenses/*.txt``.
    Matching of the file paths is implemented using the ``match`` function of Python's
    ``Path`` objects. This means, matching is performed from the end of the path. Search
    patterns are case-insensitive.

    Files are tagged using the name of the file name pattern's "group" as the keyword.
    If a file matches multiple patterns, all appropriate keywords are added. Files that
    were tagged with ``readme`` are added to the data model as a ``schema:URL`` using
    the ``codemeta:readme`` property. Files that were tagged ``license`` are added to
    the data model as a ``schema:URL`` using the ``schema:readme`` property. All found
    files that contain at least one tag are added to the data model as a
    ``schema:CreativeWork`` using the ``schema:hasPart`` property. Files that don't
    match any pattern (and thus don't have a tag) are not added to the data model. All
    file URLs are given using the ``file:`` protocol and the absolute path of the file
    at the time of harvesting.

    If available, ``git ls-files`` is used to find all files of the repository. This can
    be disabled via the options. As a fallback, the working directory is searched
    recursively for all files.
    """

    settings_class = FileExistsHarvestSettings

    # key: group name (used as keywords when tagging), value: list of patterns
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
        # mapping from file name pattern to set of tags
        self.search_pattern_keywords: Dict[str, Set[str]] = defaultdict(set)
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
                self.search_pattern_keywords[pattern].add(key)

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

        The files are tagged using the "groups" of search pattern as the keywords.
        """
        files = None
        if self.settings.enable_git_ls_files:
            files = _git_ls_files(self.working_directory)
        if files is None:
            files = self.working_directory.rglob("*")
        files_with_keywords = self._tag_files(files)
        return [
            CreativeWork.from_path(file, list(keywords))
            for file, keywords in files_with_keywords.items()
        ]

    # TODO: How to handle directories?
    def _tag_files(self, paths: Iterable[Path]) -> Dict[Path, Set[str]]:
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
