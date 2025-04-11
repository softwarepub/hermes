# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import argparse
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum, auto
from importlib import metadata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import toml
from pydantic import BaseModel
from requests import HTTPError

import hermes.commands.init.util.slim_click as sc
from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.commands.init.util import (connect_github, connect_gitlab,
                                       connect_zenodo)

TUTORIAL_URL = "https://hermes.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html"


class GitHoster(Enum):
    Empty = auto()
    GitHub = auto()
    GitLab = auto()


class DepositPlatform(Enum):
    Empty = auto()
    Zenodo = auto()
    ZenodoSandbox = auto()


DepositPlatformNames: dict[DepositPlatform, str] = {
        DepositPlatform.ZenodoSandbox: "Zenodo (Sandbox)",
        DepositPlatform.Zenodo: "Zenodo",
    }


DepositPlatformUrls: dict[DepositPlatform, str] = {
        DepositPlatform.Zenodo: "https://zenodo.org/",
        DepositPlatform.ZenodoSandbox: "https://sandbox.zenodo.org/"
    }


@dataclass
class HermesInitFolderInfo:
    def __init__(self):
        self.absolute_path: str = ""
        self.has_git_folder: bool = False
        self.git_remote_url: str = ""
        self.git_base_url: str = ""
        self.used_git_hoster: GitHoster = GitHoster.Empty
        self.has_hermes_toml: bool = False
        self.has_gitignore: bool = False
        self.has_citation_cff: bool = False
        self.has_readme: bool = False
        self.current_branch: str = ""
        self.current_dir: str = ""
        self.dir_list: list[str] = []
        self.dir_folders: list[str] = []


def is_git_installed():
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def scout_current_folder() -> HermesInitFolderInfo:
    """
    This method looks at the current directory and collects all init relevant data.

    @return: HermesInitFolderInfo object containing the gathered knowledge
    """
    info = HermesInitFolderInfo()
    current_dir = os.getcwd()
    info.current_dir = current_dir
    info.absolute_path = str(current_dir)

    info.has_git_folder = os.path.isdir(os.path.join(current_dir, ".git"))
    # git-enabled project
    if info.has_git_folder:
        # Get remote name for next command
        # TODO: missing case of multiple configured remotes (should we make the user choose?)
        git_remote = str(subprocess.run(['git', 'remote'], capture_output=True, text=True).stdout).strip()
        sc.debug_info(f"git remote = {git_remote}")

        # Get remote url via Git CLI and convert it to an HTTP link in case it's an SSH remote.
        # TODO: unchecked usage of empty remote name
        info.git_remote_url = convert_remote_url(
            str(subprocess.run(['git', 'remote', 'get-url', git_remote], capture_output=True, text=True).stdout)
        )
        # TODO: missing an "else" part!
        # TODO: can't these three pieces be stitched together to only execute when there is a remote?
        # TODO: is the url parsing necessary of it's hosted on github?
        if info.git_remote_url:
            parsed_url = urlparse(info.git_remote_url)
            info.git_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            sc.debug_info(f"git base url = {info.git_base_url}")
        if "github.com" in info.git_remote_url:
            info.used_git_hoster = GitHoster.GitHub
        elif connect_gitlab.is_url_gitlab(info.git_base_url):
            info.used_git_hoster = GitHoster.GitLab

        # Extract current branch name information by parsing Git output
        # TODO: no exception or handling in case branch is empty (e.g. detached HEAD)
        # TODO: why not use git rev-parse --abbrev-ref HEAD ?
        branch_info = str(subprocess.run(['git', 'branch'], capture_output=True, text=True).stdout)
        for line in branch_info.splitlines():
            if line.startswith("*"):
                info.current_branch = line.split()[1].strip()
                break

    info.has_hermes_toml = os.path.isfile(os.path.join(current_dir, "hermes.toml"))
    info.has_gitignore = os.path.isfile(os.path.join(current_dir, ".gitignore"))
    info.has_citation_cff = os.path.isfile(os.path.join(current_dir, "CITATION.cff"))
    info.has_readme = os.path.isfile(os.path.join(current_dir, "README.md"))
    info.dir_list = os.listdir(current_dir)
    info.dir_folders = [
        f for f in info.dir_list
        if os.path.isdir(os.path.join(current_dir, f))
        and not f.startswith(".")
    ]

    return info


def download_file_from_url(url, filepath, append: bool = False):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'ab' if append else 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except HTTPError:
        sc.echo(f"No file found at {url}.", formatting=sc.Formats.FAIL)


def string_in_file(file_path, search_string: str) -> bool:
    with open(file_path, 'r', encoding='utf-8') as file:
        return any(search_string in line for line in file)


def convert_remote_url(url: str) -> str:
    """
    Takes any url produced by 'git remote get-url origin' and returns a unified version with https & without .git
    """
    url = url.strip()
    # Remove .git from the end of the url
    url = url.removesuffix(".git")
    # Convert ssh url into http url
    if re.findall(r"^.+@.+\..+:.+\/.+$", url):
        url = re.sub(r"^.+@(.+\..+):(.+\/.+)$", r"https://\1/\2", url)
    return url


def get_builtin_plugins(plugin_commands: list[str]) -> dict[str: HermesPlugin]:
    plugins = {}
    for plugin_command_name in plugin_commands:
        entry_point_group = f"hermes.{plugin_command_name}"
        group_plugins = {
            entry_point.name: entry_point.load()
            for entry_point in metadata.entry_points(group=entry_point_group)
        }
        plugins.update(group_plugins)
    return plugins


def get_handler_by_name(name: str) -> logging.Handler:
    """Own implementation of logging.getHandlerByName so that we don't require Python 3.12"""
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            if handler.get_name() == name:
                return handler
    return None


class _HermesInitSettings(BaseModel):
    """Configuration of the ``init`` command."""
    pass


class HermesInitCommand(HermesCommand):
    """ Install HERMES onto a project. """
    command_name = "init"
    settings_class = _HermesInitSettings

    def __init__(self, parser: argparse.ArgumentParser):
        super().__init__(parser)
        self.folder_info: HermesInitFolderInfo = HermesInitFolderInfo()
        self.tokens: dict = {}
        self.setup_method: str = ""
        self.deposit_platform: DepositPlatform = DepositPlatform.Empty
        self.template_base_url: str = "https://raw.githubusercontent.com"
        self.template_branch: str = "feature/init-custom-ci"
        self.template_repo: str = "softwarepub/ci-templates"
        self.template_folder: str = "init"
        self.ci_parameters: dict = {
            "deposit_zip_name": "artifact.zip",
            "deposit_zip_files": "",
            "deposit_initial": "--initial",
            "deposit_extra_files": "",
            "push_branch": "main"
        }
        self.plugin_relevant_commands = ["harvest", "deposit"]
        self.builtin_plugins: dict[str: HermesPlugin] = get_builtin_plugins(self.plugin_relevant_commands)

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('--template-branch', nargs=1, default="",
                                    help="Branch or tag of the ci-templates repository.")

    def load_settings(self, args: argparse.Namespace):
        pass

    def refresh_folder_info(self):
        sc.debug_info("Scanning folder...")
        self.folder_info = scout_current_folder()
        sc.debug_info("Scan complete.")

    def setup_file_logging(self):
        # Silence old StreamHandler
        handler = get_handler_by_name("terminal")
        if handler:
            handler.setLevel(logging.CRITICAL)
        # Set file logger level
        self.log.setLevel(level=logging.INFO)
        # Connect logger with sc
        sc.default_file_logger = self.log

    def __call__(self, args: argparse.Namespace) -> None:
        # Setup logging
        self.setup_file_logging()

        # Save command parameter (template branch)
        if hasattr(args, "template_branch"):
            if args.template_branch != "":
                self.template_branch = args.template_branch

        # Test if init is valid in current folder
        self.test_initialization()

        sc.echo(f"Starting to initialize HERMES in {self.folder_info.absolute_path} ...")
        sc.max_steps = 7

        sc.next_step("Configure deposition platform and setup method")
        self.choose_deposit_platform()
        self.choose_setup_method()

        sc.next_step("Configure HERMES behaviour")
        self.choose_push_branch()
        self.choose_deposit_files()

        sc.next_step("Create hermes.toml file")
        self.create_hermes_toml()

        sc.next_step("Create CITATION.cff file")
        self.create_citation_cff()

        sc.next_step("Create git CI files")
        self.update_gitignore()
        self.create_ci_template()

        sc.next_step("Connect with deposition platform")
        self.connect_deposit_platform()

        sc.next_step("Connect with git project")
        self.configure_git_project()

        sc.echo("\nHERMES is now initialized and ready to be used.\n", formatting=sc.Formats.OKGREEN+sc.Formats.BOLD)

    def test_initialization(self):
        """Test if init is possible and wanted. If not: sys.exit()"""
        # Abort if git is not installed
        if not is_git_installed():
            sc.echo("Git is currently not installed. It is recommended to use HERMES with git.",
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()

        # Look at the current folder
        self.refresh_folder_info()

        # Abort if there is no git
        if not self.folder_info.has_git_folder:
            sc.echo("The current directory has no `.git` subdirectory. "
                    "Please execute `hermes init` in the root directory of your git project.",
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()

        # Abort if neither GitHub nor gitlab is used
        if self.folder_info.used_git_hoster == GitHoster.Empty:
            sc.echo("Your git project ({}) is not connected to GitHub or GitLab. It is recommended for HERMES to "
                    "use one of those hosting services.".format(self.folder_info.git_remote_url),
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()
        else:
            sc.echo(f"Git project using {self.folder_info.used_git_hoster.name} detected.\n")

        # Abort if there is already a hermes.toml
        if self.folder_info.has_hermes_toml:
            sc.echo("The current directory already has a `hermes.toml`. "
                    "It seems like HERMES was already initialized for this project.", formatting=sc.Formats.WARNING)
            if not sc.confirm("Do you want to initialize Hermes anyway? "
                              "(Hermes config files and related project variables will be overwritten.) "):
                sys.exit()

    def create_hermes_toml(self):
        """Creates the hermes.toml file based on a dictionary"""
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
                or sc.confirm("Do you want to replace your `hermes.toml` with a new one?", default=True):
            with open('hermes.toml', 'w') as toml_file:
                # noinspection PyTypeChecker
                toml.dump(default_values, toml_file)
            sc.echo("`hermes.toml` was created.", formatting=sc.Formats.OKGREEN)

    def create_citation_cff(self):
        """If there is no CITATION.cff, the user gets the opportunity to create one online."""
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
                    sc.echo("Good job!", formatting=sc.Formats.OKGREEN)
                else:
                    sc.echo("There is still no `CITATION.cff` file. Don't forget to add it later!",
                            formatting=sc.Formats.WARNING)
            else:
                sc.echo("You better do it later or HERMES won't work properly.")
                sc.echo("You can {} to create the file. Then move it into the project folder.".format(
                    sc.create_console_hyperlink(citation_cff_url, "use this website")))
        else:
            sc.echo("Your project already contains a `CITATION.cff` file. Nice!", formatting=sc.Formats.OKGREEN)

    def update_gitignore(self):
        """Creates .gitignore if there is none and adds '.hermes' to it"""
        if not self.folder_info.has_gitignore:
            open(".gitignore", 'w')
            sc.echo("A new `.gitignore` file was created.", formatting=sc.Formats.OKGREEN)
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
                    file.write("hermes.log\n")
                sc.echo("Added `.hermes/` to the `.gitignore` file.", formatting=sc.Formats.OKGREEN)

    def get_template_url(self, filename: str) -> str:
        return (f"{self.template_base_url}/{self.template_repo}/refs/heads/"
                f"{self.template_branch}/{self.template_folder}/{filename}")

    def create_ci_template(self):
        """Downloads and configures the ci workflow files using templates from the chosen template branch"""
        match self.folder_info.used_git_hoster:
            case GitHoster.GitHub:
                # TODO Replace this later with the link to the real templates (not the feature branch)
                template_url = self.get_template_url("TEMPLATE_hermes_github_to_zenodo.yml")
                ci_file_folder = ".github/workflows"
                ci_file_name = "hermes_github.yml"
                Path(ci_file_folder).mkdir(parents=True, exist_ok=True)
                ci_file_path = Path(ci_file_folder) / ci_file_name
                download_file_from_url(template_url, ci_file_path)
                self.configure_ci_template(ci_file_path)
                sc.echo(f"GitHub CI: File was created at {ci_file_path}", formatting=sc.Formats.OKGREEN)
            case GitHoster.GitLab:
                gitlab_ci_template_url = self.get_template_url("TEMPLATE_hermes_gitlab_to_zenodo.yml")
                hermes_ci_template_url = self.get_template_url("hermes-ci.yml")
                gitlab_ci_path = Path(".gitlab-ci.yml")
                Path("gitlab").mkdir(parents=True, exist_ok=True)
                hermes_ci_path = Path("gitlab") / "hermes-ci.yml"
                if gitlab_ci_path.exists():
                    if string_in_file(gitlab_ci_path, "hermes-ci.yml"):
                        sc.echo(f"It seems like your {gitlab_ci_path} file is already configured for hermes.")
                    else:
                        download_file_from_url(gitlab_ci_template_url, gitlab_ci_path, append=True)
                        sc.echo(f"GitLab CI: {gitlab_ci_path} was updated.", formatting=sc.Formats.OKGREEN)
                else:
                    download_file_from_url(gitlab_ci_template_url, gitlab_ci_path)
                    sc.echo(f"GitLab CI: {gitlab_ci_path} was created.", formatting=sc.Formats.OKGREEN)
                self.configure_ci_template(gitlab_ci_path)
                download_file_from_url(hermes_ci_template_url, hermes_ci_path)
                self.configure_ci_template(hermes_ci_path)

                # When using gitlab.com we need to use gitlab-org-docker as tag
                if "gitlab.com" in self.folder_info.git_remote_url:
                    with open(hermes_ci_path, 'r') as file:
                        content = file.read()
                    new_content = re.sub(r'(tags:\n\s+- )docker', r'\1gitlab-org-docker', content)
                    with open(hermes_ci_path, 'w') as file:
                        file.write(new_content)

                sc.echo(f"GitLab CI: {hermes_ci_path} was created.", formatting=sc.Formats.OKGREEN)

    def configure_ci_template(self, ci_file_path):
        """Replaces all {%parameter%} in a ci file with values from ci_parameters dict"""
        with open(ci_file_path, 'r') as file:
            content = file.read()
        parameters = list(set(re.findall(r'{%(.*?)%}', content)))
        for parameter in parameters:
            if parameter in self.ci_parameters:
                content = content.replace(f'{{%{parameter}%}}', self.ci_parameters[parameter])
            else:
                sc.echo(f"Warning: CI File Parameter {{%{parameter}%}} was not set.",
                        formatting=sc.Formats.WARNING)
        with open(ci_file_path, 'w') as file:
            file.write(content)

    def get_zenodo_token(self):
        self.tokens[self.deposit_platform] = ""
        # Deactivated Zenodo OAuth as long as the refresh token bug is not fixed.
        if self.setup_method == "a":
            sc.echo("Doing OAuth with Zenodo is currently not available.")
        if self.setup_method == "m" or self.tokens[self.deposit_platform] == '':
            zenodo_token_url = urljoin(DepositPlatformUrls[self.deposit_platform],
                                       "account/settings/applications/tokens/new/")
            sc.echo("{} and create an access token.".format(
                sc.create_console_hyperlink(zenodo_token_url, "Open this link")
            ))
            sc.echo("It needs the scopes \"deposit:actions\" and \"deposit:write\".")
            if self.setup_method == "m":
                sc.press_enter_to_continue()
            else:
                while True:
                    self.tokens[self.deposit_platform] = sc.answer("Enter the token here: ")
                    valid = connect_zenodo.test_if_token_is_valid(self.tokens[self.deposit_platform])
                    if valid:
                        sc.echo(f"The token was validated by {connect_zenodo.name}.",
                                formatting=sc.Formats.OKGREEN)
                        break
                    else:
                        sc.echo(f"The token could not be validated by {connect_zenodo.name}. "
                                "Make sure to enter the complete token.\n"
                                "(If this error persists, you should try switching to the manual setup mode.)",
                                formatting=sc.Formats.WARNING)

    def configure_git_project(self):
        """Adding the token to the git secrets & changing action workflow settings"""
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
                sc.echo("OAuth at GitHub was successful.", formatting=sc.Formats.OKGREEN)
                sc.debug_info(github_token=self.tokens[GitHoster.GitHub])
                connect_github.create_secret(self.folder_info.git_remote_url, "ZENODO_SANDBOX",
                                             secret_value=self.tokens[self.deposit_platform],
                                             token=self.tokens[GitHoster.GitHub])
                connect_github.allow_actions(self.folder_info.git_remote_url,
                                             token=self.tokens[GitHoster.GitHub])
                oauth_success = True
            else:
                sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.",
                        formatting=sc.Formats.WARNING)
        if not oauth_success:
            sc.echo("Add the {} token{} to your {} under the name ZENODO_SANDBOX.".format(
                self.deposit_platform.name,
                f" ({self.tokens[self.deposit_platform]})" if self.tokens[self.deposit_platform] else "",
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url + "/settings/secrets/actions",
                    "project's GitHub secrets"
                )
            ))
            sc.press_enter_to_continue()
            sc.echo("Next open your {} and check the checkbox which reads:".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url + "/settings/actions", "project settings"
                )
            ))
            sc.echo("Allow GitHub Actions to create and approve pull requests")
            sc.press_enter_to_continue()

    def configure_gitlab(self):
        # Doing it with API / OAuth
        oauth_success = False
        if self.setup_method == "a":
            gl = connect_gitlab.GitLabConnection(self.folder_info.git_remote_url)
            token = ""
            if not gl.has_client():
                sc.echo("Unfortunately HERMES does not support automatic authorization with your GitLab "
                        "installment.")
                sc.echo("Go to your {} and create a new token.".format(
                    sc.create_console_hyperlink(
                        self.folder_info.git_remote_url + "/-/settings/access_tokens",
                        "project's access tokens")
                ))
                sc.echo("It needs to have the 'developer' role and 'api' + 'write_repository' scope.")
                token = sc.answer("Then paste the token here: ")
            if gl.authorize(token):
                vars_created = gl.create_variable(
                    "ZENODO_TOKEN", self.tokens[self.deposit_platform],
                    f"This token is used by Hermes to publish on {self.deposit_platform.name}."
                )
                if vars_created:
                    project_token = gl.create_project_access_token("hermes_token")
                    if project_token:
                        vars_created = gl.create_variable(
                            "HERMES_PUSH_TOKEN", project_token,
                            "This token is used by Hermes to create pull requests."
                        )
                    else:
                        vars_created = False
                oauth_success = vars_created
            if not oauth_success:
                sc.echo("Something went wrong while setting up GitLab automatically.", formatting=sc.Formats.WARNING)
                sc.echo("You will have to do it manually instead.", formatting=sc.Formats.WARNING)

        # Doing it without API
        if not oauth_success:
            sc.echo("Go to your {} and create a new token.".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url + "/-/settings/access_tokens", "project's access tokens")
            ))
            sc.echo("It needs to have the 'developer' role and 'write_repository' scope.")
            sc.press_enter_to_continue()
            sc.echo("Open your {} and go to 'Variables'".format(
                sc.create_console_hyperlink(
                    self.folder_info.git_remote_url + "/-/settings/ci_cd", "project's ci settings")
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
        """User chooses his desired deposit platform"""
        deposit_platform_list = list(DepositPlatformNames.keys())
        deposit_platform_index = sc.choose(
            "Where do you want to publish the software?", [DepositPlatformNames[dp] for dp in deposit_platform_list]
        )
        self.deposit_platform = deposit_platform_list[deposit_platform_index]

    def choose_setup_method(self):
        setup_method_index = sc.choose(
            f"How do you want to connect {DepositPlatformNames[self.deposit_platform]} "
            f"with your {self.folder_info.used_git_hoster.name} CI?",
            options=[
                "Automatically (using OAuth / Device Flow)",
                "Manually (with instructions)",
            ]
        )
        self.setup_method = ["a", "m"][setup_method_index]

    def connect_deposit_platform(self):
        """Acquires the access token of the chosen deposit platform"""
        assert self.deposit_platform != DepositPlatform.Empty
        match self.deposit_platform:
            case DepositPlatform.Zenodo:
                connect_zenodo.setup(using_sandbox=False)
                self.get_zenodo_token()
            case DepositPlatform.ZenodoSandbox:
                connect_zenodo.setup(using_sandbox=True)
                self.get_zenodo_token()

    def no_git_setup(self, start_question: str = ""):
        """Makes the init for a gitless project (basically just creating hermes.toml)"""
        if start_question == "":
            start_question = "Do you want to initialize HERMES anyways? (No CI/CD files will be created)"
        if sc.confirm(start_question):
            sc.max_steps = 2

            sc.next_step("Create hermes.toml file")
            self.create_hermes_toml()

            sc.next_step("Create CITATION.cff file")
            self.create_citation_cff()

            sc.echo("\nHERMES is now initialized (without git integration).\n",
                    formatting=sc.Formats.OKGREEN)

    def choose_push_branch(self):
        """User chooses the branch that should be used to activate the whole hermes process"""
        # TODO make it possible to choose tags as well
        push_choice = sc.choose(
            "When should the automated HERMES process start?",
            [
                f"When I push the current branch {self.folder_info.current_branch}",
                "When I push another branch",
                "When a push a specific tag (not implemented)",
            ]
        )
        if push_choice == 0:
            self.ci_parameters["push_branch"] = self.folder_info.current_branch
        elif push_choice == 1:
            self.ci_parameters["push_branch"] = sc.answer("Enter the other branch: ")
        elif push_choice == 2:
            sc.echo("Not implemented", formatting=sc.Formats.WARNING)

    def choose_deposit_files(self):
        """User chooses the files that should be included in the deposition"""
        dp_name = DepositPlatformNames[self.deposit_platform]
        add_readme = False
        if self.folder_info.has_readme:
            if sc.confirm(f"Do you want to append your README.md to the {dp_name} upload?"):
                self.ci_parameters["deposit_extra_files"] = "--file README.md "
                add_readme = True
        options = [
            "All (non hidden) folders",
            "Everything (all folders & all files)",
            "Enter a custom list of paths",
        ]
        folder_base_index: int = len(options)
        for folder in self.folder_info.dir_folders:
            options.append(f"Only {folder}/*")
        _other = ' other' if add_readme else ''
        file_choice = sc.choose(f"Which{_other} folders / files of your root directory "
                                f"should be included in the {dp_name} upload?", options=options)
        match file_choice:
            case 0:
                self.ci_parameters["deposit_zip_files"] = " ".join(self.folder_info.dir_folders)
            case 1:
                self.ci_parameters["deposit_zip_files"] = ""
            case 2:
                custom_files = []
                while True:
                    custom_path = sc.answer("Enter a path you want to include (enter nothing if you are done): ")
                    if custom_path == "":
                        break
                    if os.path.exists(os.path.join(self.folder_info.current_dir, custom_path)):
                        custom_files.append(custom_path)
                        sc.echo(f"{custom_path} has been added.", formatting=sc.Formats.OKGREEN)
                    else:
                        sc.echo(f"{custom_path} does not exist.", formatting=sc.Formats.FAIL)
                self.ci_parameters["deposit_zip_files"] = " ".join(custom_files)
            case _:
                index = int(file_choice) - folder_base_index
                if 0 <= index < len(self.folder_info.dir_folders):
                    self.ci_parameters["deposit_zip_files"] = self.folder_info.dir_folders[index]
        sc.echo("Your upload will consist of the following:")
        if add_readme:
            sc.echo("\tUnzipped:", formatting=sc.Formats.BOLD)
            sc.echo("\t\tREADME.md", formatting=sc.Formats.OKCYAN)
        sc.echo("\tZipped:", formatting=sc.Formats.BOLD)
        if self.ci_parameters["deposit_zip_files"] != "":
            for file in self.ci_parameters["deposit_zip_files"].split(" "):
                sc.echo(f"\t\t{file}", formatting=sc.Formats.OKCYAN)
        else:
            for file in self.folder_info.dir_list:
                sc.echo(f"\t\t{file}", formatting=sc.Formats.OKCYAN)
