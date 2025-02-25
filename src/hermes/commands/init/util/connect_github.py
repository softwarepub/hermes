# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import requests
from base64 import b64encode
from nacl import encoding, public

from . import slim_click as sc
from .oauth_process import OauthProcess


local_port = 8333
client_id = 'Ov23linvdC7WzHnOO2WK'
client_secret = 'empty-as-not-needed-for-public-device-flow'
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
redirect_uri = 'http://localhost:' + str(local_port) + '/callback'
scope = "repo"
device_code_url = "https://github.com/login/device/code"


def oauth_process() -> OauthProcess:
    return OauthProcess(
        name="GitHub",
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        authorize_url=authorization_base_url,
        scope=scope,
        local_port=local_port,
        device_code_url=device_code_url
    )


def get_tokens() -> dict[str: str]:
    """Starts the oauth procedure and returns collected tokens as dict"""
    return oauth_process().get_tokens()


def get_access_token() -> str:
    return get_tokens().get('access_token', '')


def allow_actions(project_url: str, token):
    # Repository details
    url_split = project_url.split('/')
    repo_owner = url_split[-2]
    repo_name = url_split[-1]

    # GitHub API URLs
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    action_permissions_url = f"{repo_url}/actions/permissions/workflow"

    # Headers for GitHub API requests
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    # Make it possible for workflows to create pull requests
    data = {
        # 'default_workflow_permissions': 'write',
        'can_approve_pull_request_reviews': True
    }

    response = requests.put(action_permissions_url, headers=headers, json=data)

    if response.status_code in [204]:
        sc.echo("Project settings updated successfully.", formatting=sc.Formats.OKGREEN)
    else:
        sc.echo(f"Failed to update project settings: {response.status_code} {response.text}",
                formatting=sc.Formats.FAIL)
        raise Exception(f"Failed to update project settings: {response.status_code} {response.text}")


def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def create_secret(project_url: str, secret_name: str, secret_value, token):
    # Repository details
    url_split = project_url.split('/')
    repo_owner = url_split[-2]
    repo_name = url_split[-1]

    # GitHub API URLs
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    public_key_url = f"{repo_url}/actions/secrets/public-key"
    secrets_url = f"{repo_url}/actions/secrets/{secret_name}"

    # Headers for GitHub API requests
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Get the public key for the repository
    response = requests.get(public_key_url, headers=headers)
    if response.status_code == 200:
        public_key_data = response.json()
        key_id = public_key_data['key_id']
        public_key = public_key_data['key']
    else:
        sc.echo(f"Failed to retrieve public key: {response.status_code} {response.text}",
                formatting=sc.Formats.FAIL)
        raise Exception(f"Failed to retrieve public key: {response.status_code} {response.text}")

    # Encrypt the secret value using the public key
    encrypted_value = encrypt_secret(public_key, secret_value)

    # Create or update the secret in the repository
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }

    response = requests.put(secrets_url, headers=headers, json=data)

    if response.status_code in [201, 204]:
        sc.echo(f"Secret '{secret_name}' created/updated successfully.", formatting=sc.Formats.OKGREEN)
    else:
        sc.echo(f"Failed to create/update secret: {response.status_code} {response.text}",
                formatting=sc.Formats.FAIL)
        raise Exception(f"Failed to create/update secret: {response.status_code} {response.text}")
