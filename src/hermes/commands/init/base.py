# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import argparse
import os
import subprocess
import requests
import toml
from pydantic import BaseModel
from hermes.commands.base import HermesCommand
import hermes.commands.init.oauth_github as oauth_github
import hermes.commands.init.oauth_zenodo as oauth_zenodo
import hermes.commands.init.github_secrets as github_secrets
import hermes.commands.init.github_permissions as github_permissions
import hermes.commands.init.slim_click as sc


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


def is_git_installed():
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


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
        for line in branch_info.splitlines():
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
    if not sc.confirm("Are you done?", default=False):
        while not sc.confirm("Are you done now?", default=True):
            pass


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
        self.tokens: dict[str: str] = {}
        self.setup_method: str = ""

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('--only-set-refresh-token', action='store_true', default=False,
                                    dest="only_refresh_token",
                                    help="Instead of the whole setup, this just stores a new refresh token as secret.")
        command_parser.add_argument("--github-token", action='store', default="", dest="github_token",
                                    help="Use this together with --only-set-refresh-token")

    def load_settings(self, args: argparse.Namespace):
        pass

    def refresh_folder_info(self):
        self.folder_info = scout_current_folder()

    def __call__(self, args: argparse.Namespace) -> None:
        # Test if init is possible and wanted. If not: sys.exit
        self.test_initialization(args)

        # Creating the hermes.toml file
        self.create_hermes_toml()

        # Creating the citation File
        self.create_citation_cff()

        # Adding .hermes to the .gitignore
        self.update_gitignore()

        # Creating the ci file
        self.create_ci_template()

        # Choosing setup method
        self.setup_method = sc.choose("How do you want to connect with Zenodo / GitHub?",
                                      [("o", "using OAuth (default)"), ("m", "doing it manually")], default="o")

        # Getting Zenodo token
        self.get_zenodo_token()

        # Adding the token to the git secrets & changing action workflow settings
        self.configure_git_project()

        sc.echo("HERMES was initialized.")

    def test_initialization(self, args: argparse.Namespace):
        # Abort if git is not installed
        if not is_git_installed():
            sc.echo("Git is currently not installed. It is mandatory for HERMES to have git installed.")
            return

        # Look at the current folder
        self.refresh_folder_info()

        # Only set the refresh-token (this is being used after the deposit)
        if args.only_refresh_token:
            if self.folder_info.uses_github:
                zenodo_refresh_token = "REFRESH_TOKEN:" + os.environ.get('ZENODO_TOKEN_REFRESH')
                github_secrets.create_secret(self.folder_info.git_remote_url, "ZENODO_SANDBOX",
                                             zenodo_refresh_token, args.github_token)
            return

        # Abort if there is no git
        if not self.folder_info.has_git:
            sc.echo("The current directory has no `.git` subdirectory. "
                    "Please execute `hermes init` in the root directory of your git project.")
            return

        # Abort if neither GitHub nor gitlab is used
        if not (self.folder_info.uses_github or self.folder_info.uses_gitlab):
            sc.echo("Your git project ({}) is not connected to github or gitlab. It is mandatory for HERMES to "
                    "use one of those hosting services.".format(self.folder_info.git_remote_url))
            return

        sc.echo(f"Starting to initialize HERMES in {self.folder_info.absolute_path}")

        # Abort if there is already a hermes.toml
        if self.folder_info.has_hermes_toml:
            sc.echo("The current directory already has a `hermes.toml`. "
                    "It seems like HERMES was already initialized for this project.")
            if not sc.confirm("Do you want to initialize Hermes anyway? "):
                return

    def create_hermes_toml(self):
        default_values = {
            "harvest": {
                "sources": ["cff"]
            },
            "deposit": {
                "target": "invenio_rdm",
                "invenio_rdm": {
                    "site_url": "https://sandbox.zenodo.org",
                    "access_right": "open"
                 }
            }
        }

        if (not self.folder_info.has_hermes_toml) \
                or sc.confirm("Do you want to replace your `hermes.toml` with a new one?", default=False):
            with open('hermes.toml', 'w') as toml_file:
                toml.dump(default_values, toml_file)
            sc.echo("`hermes.toml` was created.")

    def create_citation_cff(self):
        if not self.folder_info.has_citation_cff:
            citation_cff_url = "https://citation-file-format.github.io/cff-initializer-javascript/#/"
            sc.echo("Your project does not contain a `CITATION.cff` file (yet). It would be very helpful for "
                    "saving important metadata which is necessary for publishing.")
            create_cff_now = sc.confirm("Do you want to create a `CITATION.cff` file now?", default=True)
            if create_cff_now:
                sc.echo("{} to create the file. Then move it into the project folder before you continue.".format(
                    sc.create_console_hyperlink(citation_cff_url, "Use this website")))
                sc.press_enter_to_continue()
                self.refresh_folder_info()
                if self.folder_info.has_citation_cff:
                    sc.echo("Good job!")
                else:
                    sc.echo("There is still no `CITATION.cff` file. Don't forget to add it later!")
            else:
                sc.echo("You better do it later or HERMES won't work properly.")
                sc.echo("You can {} to create the file. Then move it into the project folder.".format(
                    sc.create_console_hyperlink(citation_cff_url, "use this website")))
        else:
            sc.echo("Your project already contains a `CITATION.cff` file. Nice!")

    def update_gitignore(self):
        if not self.folder_info.has_gitignore:
            with open(".gitignore", 'w') as file:
                pass
            sc.echo("A new `.gitignore` file was created.")
        self.refresh_folder_info()
        if self.folder_info.has_gitignore:
            with open(".gitignore", "r") as file:
                gitignore_lines = file.readlines()
            if any([line.startswith(".hermes") for line in gitignore_lines]):
                sc.echo("The `.gitignore` file already contains `.hermes/`")
            else:
                with open(".gitignore", "a") as file:
                    file.write("# Ignoring all HERMES cache files\n")
                    file.write(".hermes/\n")
                sc.echo("Added `.hermes/` to the `.gitignore` file.")

    def create_ci_template(self):
        if self.folder_info.uses_github:
            # TODO Replace this later with the link to the real templates (not the feature branch)
            github_ci_template_raw_url = ("https://raw.githubusercontent.com/softwarepub/ci-templates/feature/"
                                          "init-command/TEMPLATE_hermes_github_to_zenodo.yml")
            github_folder_path = os.path.join(os.getcwd(), ".github")
            if not os.path.isdir(github_folder_path):
                os.mkdir(github_folder_path)
            workflows_folder_path = os.path.join(github_folder_path, "workflows")
            if not os.path.isdir(workflows_folder_path):
                os.mkdir(workflows_folder_path)
            ci_file_path = os.path.join(workflows_folder_path, "hermes_github_to_zenodo.yml")
            download_file_from_url(github_ci_template_raw_url, ci_file_path)
            sc.echo(f"GitHub CI yml file was created at {ci_file_path}")

    def get_zenodo_token(self):
        self.tokens["zenodo"] = ""
        if self.setup_method == "o":
            self.tokens["zenodo"] = oauth_zenodo.get_refresh_token()
            if self.tokens["zenodo"]:
                sc.echo("OAuth at Zenodo was successful.")
                sc.echo(self.tokens["zenodo"], debug=True)
            else:
                sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.")
        if self.setup_method == "m" or self.tokens["zenodo"] == '':
            zenodo_token_url = "https://sandbox.zenodo.org/account/settings/applications/tokens/new/"
            sc.echo("{} and create an access token.".format(
                sc.create_console_hyperlink(zenodo_token_url, "Open this link")
            ))
            if self.setup_method == "m":
                sc.press_enter_to_continue()
            else:
                self.tokens["zenodo"] = sc.answer("Then enter the token here: ")

    def configure_git_project(self):
        if self.folder_info.uses_github:
            oauth_success = False
            if self.setup_method == "o":
                self.tokens["github"] = oauth_github.get_access_token()
                if self.tokens["github"]:
                    sc.echo("OAuth at GitHub was successful.")
                    sc.echo(self.tokens["github"], debug=True)
                    github_secrets.create_secret(self.folder_info.git_remote_url, "ZENODO_SANDBOX",
                                                 secret_value=self.tokens["zenodo"], token=self.tokens["github"])
                    github_permissions.allow_actions(self.folder_info.git_remote_url, token=self.tokens["github"])
                    oauth_success = True
                else:
                    sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.")
            if not oauth_success:
                sc.echo("Now add {} to your {} under the name ZENODO_SANDBOX.".format(
                    f"the token ({self.tokens["zenodo"]})" if self.tokens["zenodo"] else "the token",
                    sc.create_console_hyperlink(
                        self.folder_info.git_remote_url.replace(".git", "/settings/secrets/actions"),
                        "project's GitHub secrets"
                    )
                ))
                sc.press_enter_to_continue()
                sc.echo("Next go to your {} and check the checkbox which reads:".format(
                    sc.create_console_hyperlink(self.folder_info.git_remote_url.replace(".git", "/settings/actions"),
                                                "project settings")
                ))
                sc.echo("Allow GitHub Actions to create and approve pull requests")
                sc.press_enter_to_continue()
                sc.echo("Good job!")
        elif self.folder_info.uses_gitlab:
            print("GITLAB INIT NOT IMPLEMENTED YET")
