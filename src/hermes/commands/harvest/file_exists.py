# SPDX-FileCopyrightText: 2025 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path
from typing import List
from typing_extensions import Self

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
            "@data": self.url,
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


class FileExistsHarvestPlugin(HermesHarvestPlugin):
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

    def __call__(self, command: HermesHarvestCommand):
        self.working_directory = command.args.path.resolve()

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
        results = set()
        for pattern in file_name_patterns:
            paths = self.working_directory.rglob(pattern, case_sensitive=False)
            results.update(paths)
        return [CreativeWork.from_path(file) for file in results]
