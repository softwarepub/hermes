# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import argparse
import os
import subprocess
import sys
import requests
import toml
from enum import Enum, auto
from urllib.parse import urlparse
from pathlib import Path
from pydantic import BaseModel
from hermes.commands.base import HermesCommand
import hermes.commands.init.connect_with_github as connect_github
import hermes.commands.init.connect_with_gitlab as connect_gitlab
import hermes.commands.init.connect_with_zenodo as connect_zenodo
import hermes.commands.init.slim_click as sc


TUTORIAL_URL = "https://docs.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html"


class GitHoster(Enum):
    Empty = auto()
    GitHub = auto()
    GitLab = auto()


class DepositPlatform(Enum):
    Empty = auto()
    Zenodo = auto()
    ZenodoSandbox = auto()


DepositPlatformChars: dict[DepositPlatform, str] = {
        DepositPlatform.Zenodo: "z",
        DepositPlatform.ZenodoSandbox: "s"
    }


DepositPlatformUrls: dict[DepositPlatform, str] = {
        DepositPlatform.Zenodo: "https://zenodo.org/",
        DepositPlatform.ZenodoSandbox: "https://sandbox.zenodo.org/"
    }


class HermesInitFolderInfo:
    def __init__(self):
        self.absolute_path: str = ""
        self.has_git: bool = False
        self.git_remote_url: str = ""
        self.git_base_url: str = ""
        self.used_git_hoster: GitHoster = GitHoster.Empty
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
        git_remote = str(subprocess.run(['git', 'remote'], capture_output=True, text=True).stdout).strip()
        sc.echo(f"git remote = {git_remote}", debug=True)
        info.git_remote_url = str(subprocess.run(['git', 'remote', 'get-url', git_remote],
                                                 capture_output=True, text=True).stdout).strip()
        sc.echo(f"git remote url = {info.git_remote_url}", debug=True)
        branch_info = str(subprocess.run(['git', 'branch'], capture_output=True, text=True).stdout)
        for line in branch_info.splitlines():
            if line.startswith("*"):
                info.current_branch = line.split()[1].strip()
                break
        if info.git_remote_url:
            parsed_url = urlparse(info.git_remote_url)
            info.git_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            sc.echo(f"git base url = {info.git_base_url}", debug=True)
    if "github.com" in info.git_remote_url:
        info.used_git_hoster = GitHoster.GitHub
    elif "401" in subprocess.run(['curl', info.git_base_url + "api/v4/version"],
                                 capture_output=True, text=True).stdout:
        info.used_git_hoster = GitHoster.GitLab
    info.has_hermes_toml = os.path.isfile(os.path.join(current_dir, "hermes.toml"))
    info.has_gitignore = os.path.isfile(os.path.join(current_dir, ".gitignore"))
    info.has_citation_cff = os.path.isfile(os.path.join(current_dir, "CITATION.cff"))
    return info


def wait_until_the_user_is_done():
    if not sc.confirm("Are you done?", default=False):
        while not sc.confirm("Are you done now?", default=True):
            pass


def download_file_from_url(url, filepath, append: bool = False):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filepath, 'ab' if append else 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def string_in_file(file_path, search_string: str) -> bool:
    with open(file_path, 'r', encoding='utf-8') as file:
        return any(search_string in line for line in file)


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
        self.deposit_platform: DepositPlatform = DepositPlatform.Empty

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('--only-set-refresh-token', action='store_true', default=False,
                                    dest="only_refresh_token",
                                    help="Instead of the whole setup, this just stores a new refresh token as secret.")
        command_parser.add_argument("--github-token", action='store', default="", dest="github_token",
                                    help="Use this together with --only-set-refresh-token")

    def load_settings(self, args: argparse.Namespace):
        pass

    def refresh_folder_info(self):
        sc.echo("Scanning folder...", debug=True)
        self.folder_info = scout_current_folder()
        sc.echo("Scan complete.", debug=True)

    def __call__(self, args: argparse.Namespace) -> None:
        sc.echo("Starting hermes init...", debug=True)

        # Test if init is possible and wanted. If not: sys.exit
        self.test_initialization(args)

        # Choosing desired deposit platform
        self.choose_deposit_platform()

        # Choosing setup method
        self.setup_method = sc.choose(
            f"How do you want to setup {self.deposit_platform.name} and the {self.folder_info.used_git_hoster.name} CI?",
            {"a": "automatically (using OAuth / Device Flow)", "m": "manually (with instructions)"}, default="a"
        )

        # Creating the hermes.toml file
        self.create_hermes_toml()

        # Creating the citation File
        self.create_citation_cff()

        # Adding .hermes to the .gitignore
        self.update_gitignore()

        # Creating the ci file
        self.create_ci_template()

        # Connect with deposit platform
        self.connect_deposit_platform()

        # Adding the token to the git secrets & changing action workflow settings
        self.configure_git_project()

        sc.echo("HERMES was initialized.")

    def test_initialization(self, args: argparse.Namespace):
        # Abort if git is not installed
        if not is_git_installed():
            sc.echo("Git is currently not installed. It is mandatory for HERMES to have git installed.")
            sys.exit()

        # Look at the current folder
        self.refresh_folder_info()

        # Only set the refresh-token (this is being used after the deposit)
        if args.only_refresh_token:
            match self.folder_info.used_git_hoster:
                case GitHoster.GitHub:
                    zenodo_refresh_token = "REFRESH_TOKEN:" + os.environ.get('ZENODO_TOKEN_REFRESH')
                    connect_github.create_secret(self.folder_info.git_remote_url, "ZENODO_SANDBOX",
                                                 zenodo_refresh_token, args.github_token)
            sys.exit()

        # Abort if there is no git
        if not self.folder_info.has_git:
            sc.echo("The current directory has no `.git` subdirectory. "
                    "Please execute `hermes init` in the root directory of your git project.")
            sys.exit()

        # Abort if neither GitHub nor gitlab is used
        if self.folder_info.used_git_hoster == GitHoster.Empty:
            sc.echo("Your git project ({}) is not connected to github or gitlab. It is mandatory for HERMES to "
                    "use one of those hosting services.".format(self.folder_info.git_remote_url))
            sys.exit()
        else:
            sc.echo(f"Git project using {self.folder_info.used_git_hoster.name} detected.")

        sc.echo(f"Starting to initialize HERMES in {self.folder_info.absolute_path}")

        # Abort if there is already a hermes.toml
        if self.folder_info.has_hermes_toml:
            sc.echo("The current directory already has a `hermes.toml`. "
                    "It seems like HERMES was already initialized for this project.")
            if not sc.confirm("Do you want to initialize Hermes anyway? "):
                sys.exit()

    def create_hermes_toml(self):
        deposit_url = DepositPlatformUrls.get(self.deposit_platform)
        default_values = {
            "harvest": {
                "sources": ["cff"]
            },
            "deposit": {
                "target": "invenio_rdm",
                "invenio_rdm": {
                    "site_url": deposit_url,
                    "access_right": "open"
                 }
            }
        }

        if (not self.folder_info.has_hermes_toml) \
                or sc.confirm("Do you want to replace your `hermes.toml` with a new one?", default=False):
            with open('hermes.toml', 'w') as toml_file:
                # noinspection PyTypeChecker
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
            open(".gitignore", 'w')
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
        match self.folder_info.used_git_hoster:
            case GitHoster.GitHub:
                # TODO Replace this later with the link to the real templates (not the feature branch)
                template_url = ("https://raw.githubusercontent.com/softwarepub/ci-templates/refs/heads/"
                                "feature/init-command/TEMPLATE_hermes_github_to_zenodo.yml")
                ci_file_folder = ".github/workflows"
                ci_file_name = "hermes_github.yml"
                Path(ci_file_folder).mkdir(parents=True, exist_ok=True)
                ci_file_path = Path(ci_file_folder) / ci_file_name
                download_file_from_url(template_url, ci_file_path)
                sc.echo(f"GitHub CI file was created at {ci_file_path}")
            case GitHoster.GitLab:
                gitlab_ci_template_url = ("https://raw.githubusercontent.com/softwarepub/ci-templates/refs/heads/"
                                          "feature/init-command/TEMPLATE_hermes_gitlab_to_zenodo.yml")
                hermes_ci_template_url = ("https://raw.githubusercontent.com/softwarepub/ci-templates/refs/heads/"
                                          "feature/init-command/gitlab/hermes-ci.yml")
                gitlab_ci_path = Path(".gitlab-ci.yml")
                Path(".gitlab").mkdir(parents=True, exist_ok=True)
                hermes_ci_path = Path(".gitlab") / "hermes-ci.yml"
                if gitlab_ci_path.exists():
                    if string_in_file(gitlab_ci_path, "hermes-ci.yml"):
                        sc.echo(f"It seems like your {gitlab_ci_path} file is already configured for hermes.")
                    else:
                        download_file_from_url(gitlab_ci_template_url, gitlab_ci_path, append=True)
                        sc.echo(f"{gitlab_ci_path} was updated.")
                else:
                    download_file_from_url(gitlab_ci_template_url, gitlab_ci_path)
                    sc.echo(f"{gitlab_ci_path} was created.")
                download_file_from_url(hermes_ci_template_url, hermes_ci_path)
                sc.echo(f"{hermes_ci_path} was created.")

    def get_zenodo_token(self, sandbox: bool = True):
        self.tokens[self.deposit_platform] = ""
        if self.setup_method == "a":
            connect_zenodo.setup(sandbox)
            self.tokens[self.deposit_platform] = connect_zenodo.get_refresh_token()
            if self.tokens[self.deposit_platform]:
                sc.echo("OAuth at Zenodo was successful.")
                sc.echo(self.tokens[self.deposit_platform], debug=True)
            else:
                sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.")
        if self.setup_method == "m" or self.tokens[self.deposit_platform] == '':
            zenodo_token_url = "https://sandbox.zenodo.org/account/settings/applications/tokens/new/" if sandbox else \
                               "https://zenodo.org/account/settings/applications/tokens/new/"
            sc.echo("{} and create an access token.".format(
                sc.create_console_hyperlink(zenodo_token_url, "Open this link")
            ))
            if self.setup_method == "m":
                sc.press_enter_to_continue()
            else:
                self.tokens[self.deposit_platform] = sc.answer("Then enter the token here: ")

    def configure_git_project(self):
        match self.folder_info.used_git_hoster:
            case GitHoster.GitHub:
                self.configure_github()
            case GitHoster.GitLab:
                self.configure_gitlab()

    def configure_github(self):
        oauth_success = False
        if self.setup_method == "a":
            self.tokens[GitHoster.GitHub] = connect_github.get_access_token()
            if self.tokens[GitHoster.GitHub]:
                sc.echo("OAuth at GitHub was successful.")
                sc.echo(self.tokens[GitHoster.GitHub], debug=True)
                connect_github.create_secret(self.folder_info.git_remote_url, "ZENODO_SANDBOX",
                                             secret_value=self.tokens[self.deposit_platform],
                                             token=self.tokens[GitHoster.GitHub])
                connect_github.allow_actions(self.folder_info.git_remote_url,
                                             token=self.tokens[GitHoster.GitHub])
                oauth_success = True
            else:
                sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.")
        if not oauth_success:
            sc.echo("Add the {} token{} to your {} under the name ZENODO_SANDBOX.".format(
                self.deposit_platform.name,
                f" ({self.tokens[self.deposit_platform]})" if self.tokens[self.deposit_platform] else "",
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url.replace(".git", "/settings/secrets/actions"),
                    "project's GitHub secrets"
                )
            ))
            sc.press_enter_to_continue()
            sc.echo("Next open your {} and check the checkbox which reads:".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url.replace(".git", "/settings/actions"),
                    "project settings"
                )
            ))
            sc.echo("Allow GitHub Actions to create and approve pull requests")
            sc.press_enter_to_continue()
            sc.echo("Good job!")

    def configure_gitlab(self):
        oauth_success = False
        if self.setup_method == "a":
            gl = connect_gitlab.GitLabConnection(self.folder_info.git_remote_url)
            if not gl.has_client():
                sc.echo("Unfortunately HERMES does not support automatic authorization with your GitLab "
                        "installment.")
                sc.echo("Go to your {} and create a new token.".format(
                    sc.create_console_hyperlink(
                        self.folder_info.git_remote_url.replace(".git", "/-/settings/access_tokens"),
                        "project's access tokens")
                ))
                sc.echo("It needs to have the 'developer' role and 'api' + 'write_repository' scope.")
                token = sc.answer("Then paste the token here: ")
                # TODO Make that token do something
            if gl.authorize():
                vars_created = gl.create_variable(
                    "ZENODO_TOKEN", self.tokens[self.deposit_platform],
                    f"This token is used by Hermes to publish on {self.deposit_platform.name}."
                )
                token = gl.create_project_access_token("hermes_token")
                if token:
                    vars_created = vars_created and gl.create_variable(
                        "HERMES_PUSH_TOKEN", token,
                        "This token is used by Hermes to create pull requests."
                    )
                else:
                    vars_created = False
                oauth_success = vars_created
            if not oauth_success:
                sc.echo("Something went wrong while setting up GitLab automatically.")
                sc.echo("You will have to do it manually instead.")
        if not oauth_success:
            sc.echo("Go to your {} and create a new token.".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url.replace(".git", "/-/settings/access_tokens"),
                    "project's access tokens")
            ))
            sc.echo("It needs to have the 'developer' role and 'write_repository' scope.")
            sc.press_enter_to_continue()
            sc.echo("Open your {} and go to 'Variables'".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url.replace(".git", "/-/settings/ci_cd"),
                    "project's ci settings")
            ))
            sc.echo("Then, add that token as variable with key HERMES_PUSH_TOKEN.")
            sc.echo("(For your safety, you should set the visibility to 'Masked'.)")
            sc.press_enter_to_continue()
            sc.echo("Next, add the {} token{} as variable with key ZENODO_TOKEN.".format(
                self.deposit_platform.name,
                f" ({self.tokens[self.deposit_platform]})" if self.tokens[self.deposit_platform] else ""
            ))
            sc.echo("(For your safety, you should set the visibility to 'Masked'.)")
            sc.press_enter_to_continue()

    def choose_deposit_platform(self):
        deposit_platform_char = sc.choose(
            "Where do you want to publish the software?",
            {DepositPlatformChars[dp]: dp.name for dp in DepositPlatformChars.keys()},
            default=DepositPlatformChars[DepositPlatform.ZenodoSandbox]
        )
        self.deposit_platform = next((dp for dp, c in DepositPlatformChars.items() if c == deposit_platform_char),
                                     DepositPlatform.Empty)

    def connect_deposit_platform(self):
        assert self.deposit_platform != DepositPlatform.Empty
        match self.deposit_platform:
            case DepositPlatform.Zenodo:
                self.get_zenodo_token(False)
            case DepositPlatform.ZenodoSandbox:
                self.get_zenodo_token(True)
