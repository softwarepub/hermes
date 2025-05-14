# SPDX-FileCopyrightText: 2025 OFFIS e.V.
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

import pathlib
import re
import requests
import tempfile
import typing as t
import os

from hermes.utils import hermes_user_agent

session = requests.Session()
session.headers.update({"User-Agent": hermes_user_agent})

def normalize_url(path: str) -> str:
    """Normalize a given URL by correcting backslashes and fixing malformed HTTPS."""
    corrected_url = path.replace("\\", "/")
    return corrected_url.replace("https:/", "https://")


def fetch_metadata_from_repo(repo_url: str, filename: str) -> t.Optional[t.Tuple[pathlib.Path, tempfile.TemporaryDirectory]]:
    """
    Fetch a metadata file (e.g., CITATION.cff or codemeta.json) from a GitHub or GitLab repository.

    :param repo_url: The repository URL.
    :param filename: The name of the metadata file to fetch.
    :return: Tuple of (Path to the temporary file, TemporaryDirectory object) or None.
    """
    try:
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = pathlib.Path(temp_dir_obj.name)

        if "github.com" in repo_url:
            # GitHub API
            api_url = repo_url.replace("github.com", "api.github.com/repos").rstrip("/") + "/contents"
            response = session.get(api_url)
            if response.status_code == 200:
                for file_info in response.json():
                    if file_info["name"] == filename:
                        temp_file = _download_to_tempfile(file_info["download_url"], filename, temp_dir)
                        return temp_file, temp_dir_obj
        elif "gitlab.com" in repo_url:
            # GitLab API
            match = re.match(r"https://([^/]+)/([^/]+)/([^/]+)", repo_url)
            if match:
                base_domain = match.group(1)
                group_or_user = match.group(2)
                project_name = match.group(3).split('/')[0]
                project_path = f"{group_or_user}/{project_name}"
                api_url = f"https://{base_domain}/api/v4/projects/{requests.utils.quote(project_path, safe='')}/repository/tree"

                response = session.get(api_url)
                if response.status_code == 200:
                    for file_info in response.json():
                        if file_info["name"] == filename:
                            file_url = (
                                f"https://{base_domain}/api/v4/projects/"
                                f"{requests.utils.quote(project_path, safe='')}/repository/files/"
                                f"{requests.utils.quote(filename, safe='')}/raw"
                            )
                            temp_file = _download_to_tempfile(file_url, filename, temp_dir)
                            return temp_file, temp_dir_obj
        else:
            print(f"Unsupported repository URL: {repo_url}")
            temp_dir_obj.cleanup()
            return None
    except Exception as e:
        print(f"Error fetching metadata from repository: {e}")
        return None


def _download_to_tempfile(url: str, filename: str, temp_dir: tempfile.TemporaryDirectory) -> pathlib.Path:
    """
    Download a file from a URL and save it to a temporary directory.

    :param url: The URL to download from.
    :param filename: The name of the file to save.
    :param temp_dir: TemporaryDirectory where the file will be saved.
    :return: Path to the temporary file.
    """
    try:
        response = session.get(url) 
        if response.status_code == 200:
            content = requests.get(url).text
            file_path = temp_dir / filename 
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return pathlib.Path(file_path)
        else:
            print(f"Failed to download {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None