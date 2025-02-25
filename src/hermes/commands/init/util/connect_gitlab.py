# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import requests
from urllib.parse import urlparse, urljoin, quote
from datetime import datetime, timedelta

from . import slim_click as sc
from .oauth_process import OauthProcess


default_scopes = "api write_repository"
device_code_addition = "oauth/authorize_device"
token_addition = "oauth/token"

site_specific_oauth_clients = [
    {
        "url": "https://gitlab.com/",
        "client_id": "1133e9cee188c31bd68c9d0e8531774a4aae9d2458e13d83e67991213f868007",
        "name_addition": "gitlab.com"
    }, {
        "url": "https://jugit.fz-juelich.de/",
        "client_id": "11a7e4215747574199db639e58b95093f7d47a6d202ed7026acf40c1c5bee4b5",
        "name_addition": "jugit"
    }, {
        "url": "https://codebase.helmholtz.cloud/",
        "client_id": "24722afbaa0d7c09566902879811c6552afa6a0bbd2cc421ab3e89af4faa2ed8",
        "name_addition": "helmholtz"
    }
]


def is_url_gitlab(url: str) -> bool:
    parsed_url = urlparse(url)
    return requests.get(f"{parsed_url.scheme}://{parsed_url.netloc}/api/v4/version").status_code == 401


class GitLabConnection:
    def __init__(self, project_url: str):
        self.project_url: str = project_url
        parsed_url = urlparse(project_url)
        self.base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        self.api_url: str = urljoin(self.base_url, "api/v4/")
        self.project_namespace_name: str = parsed_url.path.removeprefix("/")
        self.gitlab_instance_name: str = f"GitLab ({parsed_url.netloc})"
        self.client_id: str = ""
        self.access_token: str = ""
        self.project_id: str = ""
        for client in site_specific_oauth_clients:
            if client["url"] in project_url:
                self.client_id = client["client_id"]
                name_addition = client["name_addition"]
                self.gitlab_instance_name = f"GitLab ({name_addition})"
                break

    def oauth_process(self) -> OauthProcess:
        return OauthProcess(
                name=self.gitlab_instance_name,
                client_id=self.client_id,
                scope=default_scopes,
                device_code_url=self.base_url + device_code_addition,
                token_url=self.base_url + token_addition
            )

    def has_client(self) -> bool:
        return self.client_id != ""

    def authorize(self, token: str = "") -> bool:
        if token:
            # Either take the token from the parameter
            self.access_token = token
        else:
            # Or use Oauth to get access token
            self.access_token = self.oauth_process().get_tokens().get('access_token', '')
            if not self.access_token:
                return False
        # Use that token to get the project id (the token is needed since the project might be private)
        request_url = urljoin(self.api_url, f"projects/{quote(self.project_namespace_name, safe='')}")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        sc.debug_info(f"Getting project id from {request_url}")
        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            project_info = response.json()
            self.project_id = project_info["id"]
            sc.debug_info("Received project id")
            sc.debug_info(project_id=self.project_id)
            return True
        else:
            sc.echo(f"Could not get project id for {self.project_url}.")
            sc.debug_info(response_text=response.text)
            return False

    def create_project_access_token(self, name: str, scopes: list[str] = None) -> str:
        assert self.access_token
        scopes = scopes or default_scopes.split(" ")
        expire_date = datetime.now() + timedelta(days=364)
        request_url = urljoin(self.api_url, f"projects/{self.project_id}/access_tokens")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = {"name": name, "scopes": scopes, "expires_at": expire_date.strftime('%Y-%m-%d')}
        response = requests.post(request_url, headers=headers, json=data)
        if response.status_code == 201:
            response_data = response.json()
            sc.echo("Created Gitlab project access token.", formatting=sc.Formats.OKGREEN)
            sc.debug_info(response_data=response_data)
            return response_data["token"]
        else:
            sc.echo("Could not create a project access token.", formatting=sc.Formats.WARNING)
            sc.debug_info(response_text=response.text)
            sc.debug_info(response_dict=response.__dict__)
            return ""

    def create_variable(self, key: str, value, description: str = "") -> bool:
        assert self.access_token
        # First try to delete the variable if it already exists
        sc.debug_info(f"Creating Variable {key}")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        delete_url = urljoin(self.api_url, f"projects/{self.project_id}/variables/{key}")
        delete_response = requests.delete(delete_url, headers=headers)
        sc.debug_info(delete_status=delete_response.status_code, delete_response=delete_response.text)
        # Then create a new variable
        create_url = urljoin(self.api_url, f"projects/{self.project_id}/variables")
        data = {"key": key, "value": value, "masked": True, "raw": True, "description": description}
        response = requests.post(create_url, headers=headers, json=data)
        if response.status_code == 201:
            desc = f" ({description})" if description else ""
            sc.echo(f"Successfully created CI Variable {key}{desc}.", formatting=sc.Formats.OKGREEN)
            return True
        else:
            sc.echo(f"Could not create CI Variable {key}.", formatting=sc.Formats.FAIL)
            sc.debug_info(response_text=response.text)
            sc.debug_info(post_data=data, headers=headers)
            return False
