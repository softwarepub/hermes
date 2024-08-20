import os
import requests
import json
from base64 import b64encode
from nacl import encoding, public


def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def create_secret(project_url: str, secret_name: str, secret_value):
    # Access token obtained from GitHub OAuth process
    token = os.environ.get('GITHUB_TOKEN')

    # Repository details
    url_split = project_url.split('/')
    repo_owner = url_split[-2]
    repo_name = url_split[-1].replace(".git", "")

    # GitHub API URLs
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    public_key_url = f"{repo_url}/actions/secrets/public-key"
    secrets_url = f"{repo_url}/actions/secrets/{secret_name}"

    print(repo_url)
    print(public_key_url)
    print(secrets_url)

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
        print(f"Public Key Data {public_key_data}")
    else:
        raise Exception(f"Failed to retrieve public key: {response.status_code} {response.text}")

    # Encrypt the secret value using the public key
    encrypted_value = encrypt_secret(public_key, secret_value)

    # Create or update the secret in the repository
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }

    response = requests.put(secrets_url, headers=headers, data=json.dumps(data))

    if response.status_code in [201, 204]:
        print(f"Secret '{secret_name}' created/updated successfully.")
    else:
        print(f"Failed to create/update secret: {response.status_code} {response.text}")
