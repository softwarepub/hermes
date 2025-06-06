# SPDX-FileCopyrightText: 2025 OFFIS e.V.
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Stephan Ferenz
# SPDX-FileContributor: Aida Jafarbigloo

import pathlib
import requests
import tempfile
import typing as t
from urllib.parse import urlparse, quote

from hermes.utils import hermes_user_agent


def normalize_url(path: str) -> str:
    """Normalize a given URL by correcting backslashes and fixing malformed HTTPS."""
    corrected_url = path.replace("\\", "/")
    return corrected_url.replace("https:/", "https://")


def fetch_metadata_from_repo(repo_url: str, filename: str, token: str = None) -> t.Optional[t.Tuple[pathlib.Path, tempfile.TemporaryDirectory]]:
    """
    Fetch a metadata file (e.g., CITATION.cff or codemeta.json) from a GitHub or GitLab repository.

    :param repo_url: The repository URL.
    :param filename: The name of the metadata file to fetch.
    :param token: (Optional) Access token for authentication (GitHub token or GitLab private token).
    :return: A tuple containing:
             - Path to the downloaded metadata file.
             - TemporaryDirectory object (caller is responsible for cleanup).
             Returns None if the file could not be fetched.
    """
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": hermes_user_agent})
        if token:
            if "github" in repo_url:
                session.headers.update({"Authorization": f"token {token}"})
            elif "gitlab" in repo_url:
                session.headers.update({"PRIVATE-TOKEN": token})
                
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = pathlib.Path(temp_dir_obj.name)
        
        parsed_url = urlparse(repo_url)
        
        if "github.com" in repo_url:
            # GitHub API: List repository contents
            api_url = repo_url.replace("github.com", "api.github.com/repos").rstrip("/") + "/contents"
            response = session.get(api_url)
            if response.status_code == 200:
                for file_info in response.json():
                    if file_info["name"] == filename:
                        temp_file = _download_to_tempfile(file_info["download_url"], filename, temp_dir, session)
                        return temp_file, temp_dir_obj
        elif "gitlab" in parsed_url.netloc:
            # GitLab API 
            temp_file, temp_dir = _fetch_from_gitlab(parsed_url, filename, temp_dir, session)
            if temp_file:
                return temp_file, temp_dir_obj
        else:
            print(f"Unsupported repository URL: {repo_url}")
            temp_dir_obj.cleanup()
            return None

    except Exception as e:
        print(f"Error fetching metadata from repository: {e}")
        return None


def _fetch_from_gitlab(parsed_url, filename, temp_dir, session):
    """
    Helper function to fetch a file from GitLab.
    """
    base_domain = parsed_url.netloc 
    project_path = parsed_url.path.lstrip('/')  
    encoded_project_path = quote(project_path, safe='')

    # Step 1: Detect default branch
    project_api_url = f"https://{base_domain}/api/v4/projects/{encoded_project_path}"
    project_resp = session.get(project_api_url)
    if project_resp.status_code != 200:
        print(f"Failed to fetch project info: {project_resp.status_code}")
        return None, None

    project_info = project_resp.json()
    default_branch = project_info.get('default_branch', 'main')  # fallback to 'main' if not found

    # Step 2: Search for the file recursively
    page = 1
    per_page = 100
    found_file = None

    while True:
        api_url = (
            f"https://{base_domain}/api/v4/projects/{encoded_project_path}/repository/tree"
            f"?recursive=true&per_page={per_page}&page={page}"
        )
        response = session.get(api_url)
        if response.status_code != 200:
            print(f"Failed to fetch repo tree: {response.status_code}")
            break

        files_list = response.json()
        if not files_list:
            break

        for file_info in files_list:
            if file_info.get("type") == "blob" and file_info.get("name", "").lower() == filename.lower():
                found_file = file_info
                break

        if found_file:
            break

        page += 1

    # Step 3: Download the file
    if found_file:
        file_path_in_repo = found_file["path"]
        file_url = (
            f"https://{base_domain}/api/v4/projects/"
            f"{encoded_project_path}/repository/files/"
            f"{quote(file_path_in_repo, safe='')}/raw?ref={default_branch}"
        )
        temp_file = _download_to_tempfile(file_url, filename, temp_dir, session)
        if temp_file:
            print(f"Downloaded file: {temp_file}")
        return temp_file, temp_dir

    print(f"{filename} not found in repository.")
    return None, None



def _download_to_tempfile(url: str, filename: str, temp_dir: pathlib.Path, session: requests.Session) -> pathlib.Path:
    try:
        response = session.get(url)
        if response.status_code == 200:
            file_path = temp_dir / filename

            try:
                text = response.content.decode('utf-8')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            except UnicodeDecodeError:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
            return pathlib.Path(file_path)
        else:
            print(f"Failed to download {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None
