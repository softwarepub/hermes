# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import re
import os
import subprocess
from pathlib import Path


default_cwd = ""


def get_valid_cwd(cwd="") -> str:
    """
    Returns the given cwd if valid or the default_cwd / os.getcwd() when not cwd is given.
    """
    # Get default when cwd is empty
    if cwd == "":
        if default_cwd:
            cwd = default_cwd
        else:
            cwd = os.getcwd()
    # Test if valid
    path = Path(cwd)
    if not path.exists():
        raise Exception(f"Path {path} does not exist.")
    elif not path.is_dir():
        raise Exception(f"Path {path} is not a directory.")
    # Return
    return str(path)


def run_git_command(command: str, cwd="") -> str:
    """
    Runs any git command using subprocess. Raises Exception when returncode != 0.
    :param command: The command as string with or without the 'git' main command.
    :param cwd: Path to target directory ( if it differs from os.getcwd() ).
    :return: The command's output.
    """
    # Validate or get default cwd
    cwd = get_valid_cwd(cwd)
    # Get command list from string
    command_list = [s for s in command.split(" ") if s != ""]
    if command_list[0] != "git":
        command_list.insert(0, "git")
    # Run subprocess
    result = subprocess.run(command_list, cwd=cwd, capture_output=True, text=True)
    # Return output or error
    if result.returncode != 0:
        raise Exception(result.stderr)
    return str(result.stdout)


def get_remotes() -> list[str]:
    """
    Returns a list of all remotes.
    """
    git_remote_output: str = run_git_command("remote").strip()
    cleaned_remote_list = [s.strip() for s in git_remote_output.split("\n")]
    return cleaned_remote_list


def convert_remote_url(url: str) -> str:
    """
    Takes any url produced by 'git remote get-url ...' and returns a consistent version with https & without '.git'.
    """
    url = url.strip()
    # Remove .git from the end of the url
    url = url.removesuffix(".git")
    # Convert ssh-url into http-url using beautiful, human-readable regex
    if re.findall(r"^.+@.+\..+:.+\/.+$", url):
        url = re.sub(r"^.+@(.+\..+):(.+\/.+)$", r"https://\1/\2", url)
    return url


def get_remote_url(remote: str) -> str:
    """
    Returns the url of the given remote.
    """
    if remote not in get_remotes():
        raise Exception(f"Remote {remote} not found.")
    url_output = run_git_command(f"remote get-url {remote}")
    return convert_remote_url(url_output)


def get_current_branch() -> str:
    """
    Returns the name of the current branch.
    """
    branch_info = run_git_command("branch")
    for line in branch_info.splitlines():
        if line.startswith("*"):
            return line.split()[1].strip()
    raise Exception("Current branch not found.")


def is_git_installed() -> bool:
    """
    Uses the --version command to check whether git is installed.
    """
    try:
        result = subprocess.run(['git', '--version'], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False
