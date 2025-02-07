import pathlib
import re
import requests
import tempfile
import typing as t
import os

def normalize_url(path: str) -> str:
    """Normalize a given URL by correcting backslashes and fixing malformed HTTPS."""
    corrected_url = path.replace("\\", "/")
    return corrected_url.replace("https:/", "https://")


def fetch_metadata_from_repo(repo_url: str, filename: str) -> t.Optional[pathlib.Path]:
    """
    Fetch a metadata file (e.g., CITATION.cff or codemeta.json) from a GitHub or GitLab repository.

    :param repo_url: The repository URL.
    :param filename: The name of the metadata file to fetch.
    :return: Path to the temporary file containing the downloaded metadata, or None.
    """
    try:
        if "github.com" in repo_url:
            # GitHub API
            api_url = repo_url.replace("github.com", "api.github.com/repos").rstrip("/") + "/contents"
            response = requests.get(api_url)
            if response.status_code == 200:
                for file_info in response.json():
                    if file_info["name"] == filename:
                        return _download_to_tempfile(file_info["download_url"], filename)
        elif "gitlab.com" in repo_url:
            # GitLab API
            match = re.match(r"https://([^/]+)/([^/]+)/([^/]+)", repo_url)
            if match:
                base_domain = match.group(1)
                group_or_user = match.group(2)
                project_name = match.group(3).split('/')[0]
                project_path = f"{group_or_user}/{project_name}"
                api_url = f"https://{base_domain}/api/v4/projects/{requests.utils.quote(project_path, safe='')}/repository/tree"

                response = requests.get(api_url)
                if response.status_code == 200:
                    for file_info in response.json():
                        if file_info["name"] == filename:
                            file_url = (
                                f"https://{base_domain}/api/v4/projects/"
                                f"{requests.utils.quote(project_path, safe='')}/repository/files/"
                                f"{requests.utils.quote(filename, safe='')}/raw"
                            )
                            return _download_to_tempfile(file_url, filename)
        else:
            print(f"Unsupported repository URL: {repo_url}")
            return None
    except Exception as e:
        print(f"Error fetching metadata from repository: {e}")
        return None


def _download_to_tempfile(url: str, filename: str) -> pathlib.Path:
    """
    Download a file from a URL and save it to a temporary file.

    :param url: The URL to download from.
    :param filename: The name of the file to save.
    :return: Path to the temporary file.
    """
    try:
        content = requests.get(url).text
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
            temp_file.write(content.encode("utf-8"))
            print(f"Downloaded {filename} to {temp_file.name}")
            return pathlib.Path(temp_file.name)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return None


def remove_temp_file(file_path: pathlib.Path, temp_dir: pathlib.Path = pathlib.Path("C:/Temp")):
    """
    Removes a temporary file if it is inside the temp directory.

    :param file_path: The file path to check and remove.
    :param temp_dir: The directory considered as temporary (default: "C:/Temp").
    """
    if str(file_path).startswith(str(temp_dir)):
        os.remove(file_path)
