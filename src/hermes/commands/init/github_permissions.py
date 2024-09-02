import os
import requests
import json

def allow_actions(project_url: str, token = ""):
    # Access token obtained from GitHub OAuth process
    if token == "":
        token = os.environ.get('GITHUB_TOKEN')

    # Repository details
    url_split = project_url.split('/')
    repo_owner = url_split[-2]
    repo_name = url_split[-1].replace(".git", "")

    # GitHub API URLs
    repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    action_permissions_url = f"{repo_url}/actions/permissions/workflow"

    # Headers for GitHub API requests
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    # Create or update the secret in the repository
    data = {
        'default_workflow_permissions': 'write',
        'can_approve_pull_request_reviews': True
    }

    response = requests.put(action_permissions_url, headers=headers, data=json.dumps(data))

    if response.status_code in [204]:
        print(f"Project settings updated successfully.")
    else:
        print(f"Failed to update project settings: {response.status_code} {response.text}")
