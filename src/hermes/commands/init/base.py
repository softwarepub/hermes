# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import shutil
import os
import subprocess
import requests
import click
from pydantic import BaseModel

from hermes.commands.base import HermesCommand


class HermesInitFolderInfo:
    def __init__(self):
        self.absolute_path: str = ""
        self.has_git: bool = False
        self.git_remote_url: str = ""
        self.uses_github: bool = False
        self.uses_gitlab: bool = False
        self.has_hermes_toml: bool = False
        self.has_gitignore: bool = False
        self.has_citation_cff = False
        self.current_branch: str = ""


def scout_current_folder() -> HermesInitFolderInfo:
    info = HermesInitFolderInfo()
    current_dir = os.getcwd()
    info.absolute_path = str(current_dir)
    info.has_git = os.path.isdir(os.path.join(current_dir, ".git"))
    if info.has_git:
        remote_info = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, check=True).stdout
        for line in remote_info.splitlines():
            if line.startswith("origin"):
                whitespace_split = line.split()
                if len(whitespace_split) > 1:
                    info.git_remote_url = whitespace_split[1]
                    break
        branch_info = subprocess.run(['git', 'branch'], capture_output=True, text=True, check=True).stdout
        for line in remote_info.splitlines():
            if line.startswith("*"):
                info.current_branch = line.split()[1].strip()
                break
    info.uses_github = "github" in info.git_remote_url
    info.uses_gitlab = "gitlab" in info.git_remote_url
    info.has_hermes_toml = os.path.isfile(os.path.join(current_dir, "hermes.toml"))
    info.has_gitignore = os.path.isfile(os.path.join(current_dir, ".gitignore"))
    info.has_citation_cff = os.path.isfile(os.path.join(current_dir, "CITATION.cff"))
    return info


def wait_until_the_user_is_done():
    if not click.confirm("Are you done?", default=False):
        while not click.confirm("Are you done now?", default=True):
            pass


def create_console_hyperlink(url: str, word: str) -> str:
    return f"\033]8;;{url}\033\\{word}\033]8;;\033\\"


def download_file_from_url(url, filepath):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


class HermesInitSettings(BaseModel):
    """Configuration of the ``init`` command."""
    pass


class HermesInitCommand(HermesCommand):
    """ Install HERMES onto a project. """

    command_name = "init"
    settings_class = HermesInitSettings

    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)
        self.folder_info: HermesInitFolderInfo = HermesInitFolderInfo()

    def load_settings(self, args: argparse.Namespace):
        pass

    def refresh_folder_info(self):
        self.folder_info = scout_current_folder()

    def __call__(self, args: argparse.Namespace) -> None:
        self.refresh_folder_info()
        click.echo(f"Starting to initialize HERMES in {self.folder_info.absolute_path}")

        # Abort if there is already a hermes.toml
        if self.folder_info.has_hermes_toml:
            click.echo("The current directory already has a `hermes.toml`. "
                       "It seems like HERMES was already initialized for this project.")
            return

        # Abort if there is no git
        if not self.folder_info.has_git:
            click.echo("The current directory already has no `.git` subdirectory. "
                       "Please execute `hermes init` in the root directory of your git project.")
            return

        # Abort if neither GitHub nor gitlab is used
        if not (self.folder_info.uses_github or self.folder_info.uses_gitlab):
            click.echo("Your git project ({}) is not connected to github or gitlab. It is mandatory for HERMES to "
                       "use one of those hosting services.".format(self.folder_info.git_remote_url))
            return

        # Creating the citation File
        if not self.folder_info.has_citation_cff:
            citation_cff_url = "https://citation-file-format.github.io/cff-initializer-javascript/#/"
            click.echo("Your project does not contain a `CITATION.cff` file (yet). It would be very helpful for "
                       "saving important metadata which is necessary for publishing.")
            create_cff_now = click.confirm("Do you want to create a `CITATION.cff` file now?", default=True)
            if create_cff_now:
                click.echo("{} to create the file. Then move it into the project folder before you continue.".format(
                    create_console_hyperlink(citation_cff_url, "Click here")))
                done_creating_cff = click.confirm("Are you done?", default=False)
                while not done_creating_cff:
                    done_creating_cff = click.confirm("Are you done now?", default=True)
                self.refresh_folder_info()
                if self.folder_info.has_citation_cff:
                    click.echo("Good job!")
                else:
                    click.echo("Hey you lied to me :( Don't forget to add the `CITATION.cff` file later!")
            else:
                click.echo("You better do it later or HERMES won't work properly.")
                click.echo("You can {} to create the file. Then move it into the project folder.".format(
                    create_console_hyperlink(citation_cff_url, "click here")))
        else:
            click.echo("Your project already contains a `CITATION.cff` file. Nice!")

        # Creating the hermes.toml file
        hermes_toml_raw_url = "https://raw.githubusercontent.com/nheeb/zenodo-test/main/hermes.toml"
        download_file_from_url(hermes_toml_raw_url, os.path.join(os.getcwd(), "hermes.toml"))
        click.echo("hermes.toml was created.")

        # Adding .hermes to the .gitignore
        if not self.folder_info.has_gitignore:
            with open(".gitignore", 'w') as file:
                pass
            click.echo("A new `.gitignore` file was created.")
        self.refresh_folder_info()
        if self.folder_info.has_gitignore:
            with open(".gitignore", "r") as file:
                gitignore_lines = file.readlines()
            if any([line.startswith(".hermes") for line in gitignore_lines]):
                click.echo("The `.gitignore` file already contains `.hermes/`")
            else:
                with open(".gitignore", "a") as file:
                    file.write("# Ignoring all HERMES cache files")
                    file.write(".hermes/")
                click.echo("Added `.hermes/` to the `.gitignore` file.")

        # Creating the ci file
        if self.folder_info.uses_github:
            github_ci_template_raw_url = ("https://raw.githubusercontent.com/softwarepub/ci-templates/main"
                                          "/TEMPLATE_hermes_github_to_zenodo.yml")
            github_folder_path = os.path.join(os.getcwd(), ".github")
            if not os.path.isdir(github_folder_path):
                os.mkdir(github_folder_path)
            workflows_folder_path = os.path.join(github_folder_path, "workflows")
            if not os.path.isdir(workflows_folder_path):
                os.mkdir(workflows_folder_path)
            ci_file_path = os.path.join(workflows_folder_path, "hermes_github_to_zenodo.yml")
            download_file_from_url(github_ci_template_raw_url, ci_file_path)
            click.echo(f"GitHub CI yml file was created at {ci_file_path}")

        # Zenodo access token -> Github Secrets
        zenodo_token_url = "https://sandbox.zenodo.org/account/settings/applications/tokens/new/"
        click.echo("If you haven't already, {}. You might have to create an account first.".format(
            create_console_hyperlink(zenodo_token_url, "create a access token for zenodo")
        ))
        wait_until_the_user_is_done()
        if self.folder_info.uses_github:
            click.echo("Now add this token to your {} under the name ZENODO_SANDBOX.".format(
                create_console_hyperlink(self.folder_info.git_remote_url.replace(".git", "/settings/secrets/actions"),
                                         "project's GitHub secrets")
            ))
            wait_until_the_user_is_done()
            click.echo("Next go to your {} and check the checkbox which reads:".format(
                create_console_hyperlink(self.folder_info.git_remote_url.replace(".git", "/settings/actions"),
                                         "project settings")
            ))
            click.echo(click.style("Allow GitHub Actions to create and approve pull requests", bold=True))
            wait_until_the_user_is_done()
            click.echo("Good job!")
        elif self.folder_info.uses_gitlab:
            print("GITLAB INIT NOT IMPLEMENTED YET")

        click.echo("HERMES was initialized.")

