# SPDX-FileCopyrightText: 2024 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import argparse
import logging
import os
import re
import shutil
import sys
import traceback
from dataclasses import dataclass
from enum import Enum, auto
from importlib import metadata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import jinja2
import jinja2.meta
import requests
import toml
from pydantic import BaseModel
from requests import HTTPError

import hermes.commands.init.util.slim_click as sc
from hermes.commands import marketplace
from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.commands.init.util import (connect_github, connect_gitlab,
                                       connect_zenodo, git_info)

TUTORIAL_URL = "https://hermes.software-metadata.pub/en/latest/tutorials/automated-publication-with-ci.html"
REPOSITORY_URL = "https://github.com/softwarepub/hermes"


class GitHoster(Enum):
    Empty = auto()
    GitHub = auto()
    GitLab = auto()


class DepositId(Enum):
    """
    Enum as additional identifier for DepositPlatforms so we have something persistent to code with.
    """
    Empty = auto()
    Zenodo = auto()
    ZenodoSandbox = auto()
    # JuelichData = auto()
    # JuelichDataBeta = auto()
    # DemoDataverse = auto()
    Rodare = auto()
    RodareTest = auto()


@dataclass
class DepositPlatform:
    """
    This dataclass contains all relevant data to set up hermes for a given platform.
    """
    def __init__(self, name: str = "", url: str = "", plugin_name: str = "", deposit_id: DepositId = DepositId.Empty):
        self.name: str = name
        self.url: str = url
        """Base url of the deposit platform"""
        self.plugin_name: str = plugin_name
        """Internal name of our related hermes deposit plugin"""
        self.id: DepositId = deposit_id
        """Non changing enum-based ID to keep the consistency"""
        self.internal_name: str = deposit_id.name
        self.token: str = ""
        """This is the access token which will get filled in connect_deposit_platform"""
        self.token_name: str = re.sub(r'(?<!^)(?=[A-Z])', '_', self.internal_name).upper() + "_TOKEN"
        """This is the internal name in uppercase, with underscores and ending with _TOKEN.
           This is used as name for the secret variable on the GitHoster."""


DepositOptions: list[DepositPlatform] = [
    DepositPlatform("Zenodo Sandbox", "https://sandbox.zenodo.org/", "invenio_rdm", DepositId.ZenodoSandbox),
    DepositPlatform("Zenodo", "https://zenodo.org/", "invenio_rdm", DepositId.Zenodo),
    # DepositPlatform("Demo Dataverse", "https://demo.dataverse.org/", "dataverse", DepositId.DemoDataverse),
    # DepositPlatform("Jülich DATA", "https://data.fz-juelich.de/", "dataverse", DepositId.JuelichData),
    # DepositPlatform("Jülich DATA Beta", "https://data-beta.fz-juelich.de/", "dataverse", DepositId.JuelichDataBeta),
    DepositPlatform("Rodare", "https://rodare.hzdr.de/", "rodare", DepositId.Rodare),
    DepositPlatform("Rodare Test", "https://rodare-test.hzdr.de/", "rodare", DepositId.RodareTest),
]


@dataclass
class HermesInitFolderInfo:
    """
    Contains information about the current state of the target project directory.
    """
    def __init__(self):
        self.absolute_path: str = ""
        self.has_git_folder: bool = False
        self.has_hermes_toml: bool = False
        self.has_gitignore: bool = False
        self.has_citation_cff: bool = False
        self.has_readme: bool = False
        self.current_dir: str = ""
        self.dir_list: list[str] = []
        self.dir_folders: list[str] = []


def scout_current_folder() -> HermesInitFolderInfo:
    """
    This method looks at the current directory and collects all init relevant data.
    This method is not meant to contain any user interactions.
    @return: HermesInitFolderInfo object containing the gathered knowledge
    """
    info = HermesInitFolderInfo()
    current_dir = os.getcwd()
    info.current_dir = current_dir
    info.absolute_path = str(current_dir)
    info.has_git_folder = os.path.isdir(os.path.join(current_dir, ".git"))
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


def get_git_hoster_from_url(url: str) -> GitHoster:
    """
    Returns the matching GitHoster value to the given url. Returns GitHoster.Empty if none is found.
    """
    parsed_url = urlparse(url)
    git_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"  # noqa E231
    if "github.com" in url:
        return GitHoster.GitHub
    elif connect_gitlab.is_url_gitlab(git_base_url):
        return GitHoster.GitLab
    return GitHoster.Empty


def download_file_from_url(url, filepath, append: bool = False) -> None:
    if not append and os.path.exists(filepath):
        os.remove(filepath)
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


def get_builtin_plugins(plugin_commands: list[str]) -> dict[str, HermesPlugin]:
    """
    Returns a list of installed HermesPlugins based on a list of related command names.
    This is currently not used (we use the marketplace code instead) but maybe later.
    """
    plugins = {}
    for plugin_command_name in plugin_commands:
        entry_point_group = f"hermes.{plugin_command_name}"
        group_plugins = {
            entry_point.name: entry_point.load()
            for entry_point in metadata.entry_points(group=entry_point_group)
        }
        plugins.update(group_plugins)
    return plugins


def get_handler_by_name(name: str) -> logging.Handler | None:
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
        self.hermes_was_already_installed: bool = False
        self.warn_on_old_version: bool = True
        self.new_created_paths: list[Path] = []
        self.tokens: dict = {}
        self.setup_method: str = ""
        self.deposit_platform: DepositPlatform = DepositPlatform()
        self.git_branch: str = ""
        self.git_remote: str = ""
        self.git_remote_url = ""
        self.git_hoster: GitHoster = GitHoster.Empty
        self.template_base_url: str = "https://raw.githubusercontent.com"
        self.template_branch: str = "feature/jinja"
        self.template_repo: str = "softwarepub/ci-templates"
        self.template_folder: str = "init-templates"
        self.ci_parameters: dict = {
            "pip_install_hermes": "pip install hermes",
            "pip_install_plugins_github": "",
            "pip_install_plugins_gitlab": "",
            "deposit_zip_name": "artifact.zip",
            "deposit_zip_files": "",
            "deposit_initial": "--initial",
            "deposit_extra_files": "",
            "deposit_parameter_token": "-O ???.auth_token",
            "deposit_token_name": "???_TOKEN",
            "gh_push_branches_or_tags": "branches",
            "gh_push_target": "main",
            "gl_push_condition": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"
        }
        self.hermes_toml_data = {
            "harvest": {
                "sources": ["cff"]
            },
            "deposit": {
                "target": "",
            }
        }
        self.plugin_relevant_commands = ["harvest", "deposit"]
        self.builtin_plugins: dict[str, HermesPlugin] = get_builtin_plugins(self.plugin_relevant_commands)
        self.selected_plugins: list[marketplace.PluginInfo] = []

    def init_command_parser(self, command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument('--template-branch', nargs=1, default="",
                                    help="Branch or tag of the ci-templates repository.")
        command_parser.add_argument('--hermes-branch', nargs=1, default="",
                                    help="Branch of the hermes repository which will be used in the pipeline.")

    def load_settings(self, args: argparse.Namespace):
        pass

    def refresh_folder_info(self) -> None:
        """Checks the contents of the current directory and saves relevant info in self.folder_info"""
        sc.debug_info("Scanning folder...")
        self.folder_info = scout_current_folder()
        sc.debug_info("Scan complete.")

    def setup_file_logging(self) -> None:
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

        # Warning on old hermes version
        self.check_hermes_version()

        # Process command parameters (ci-templates branch & hermes branch)
        if hasattr(args, "template_branch"):
            if args.template_branch != "":
                self.template_branch = args.template_branch
        if hasattr(args, "hermes_branch"):
            if args.hermes_branch:
                branch_name = args.hermes_branch[0]
                if branch_name != "":
                    sc.echo(f"Using Hermes branch: {branch_name}")
                    self.ci_parameters["pip_install_hermes"] = \
                        f"pip install git+{REPOSITORY_URL}.git@{branch_name}"

        try:
            # Test if init is valid in current folder
            self.test_initialization()

            sc.echo(f"Starting to initialize HERMES in {self.folder_info.absolute_path}\n")
            sc.max_steps = 8

            sc.next_step("Configure HERMES plugins")
            self.choose_plugins()
            self.integrate_plugins()

            sc.next_step("Configure deposition platform and setup method")
            self.choose_deposit_platform()
            self.integrate_deposit_platform()
            self.choose_setup_method()

            sc.next_step("Configure HERMES behaviour")
            self.choose_push_trigger()
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

            sc.next_step("Connect with git hoster")
            self.configure_git_project()

            self.clean_up_files(False)
            sc.echo("\nHERMES is now initialized. Add the changes to your git index and it is ready to be used.\n",
                    formatting=sc.Formats.OKGREEN+sc.Formats.BOLD)

        # Nice message on Ctrl+C
        except KeyboardInterrupt:
            sc.echo("")
            sc.echo("HERMES init was aborted. No changes were made.", sc.Formats.WARNING)
            self.clean_up_files(True)
            sys.exit()

        # Useful message on error
        except Exception as e:
            sc.echo(f"An error occurred during execution of HERMES init: {e}",
                    formatting=sc.Formats.FAIL+sc.Formats.BOLD)
            sc.debug_info(traceback.format_exc())
            self.clean_up_files(True)
            sc.echo("No changes were made. You will have to run 'hermes init' again.")
            sys.exit(2)

    def check_hermes_version(self) -> None:
        """Fetches the current Pypi Hermes version. Gives a warning if the current version is not up to date."""
        if not self.warn_on_old_version:
            return
        try:
            current_hermes_version: str = metadata.version("hermes")
            pypi_hermes_json: dict = requests.get("https://pypi.org/pypi/hermes/json", timeout=10).json()
            pypi_hermes_version: str = pypi_hermes_json["info"]["version"]

            def version_tuple(version_string: str) -> tuple:
                version_string = re.split(r"[A-Za-z]", version_string, maxsplit=1)[0]
                return tuple(int(p) for p in version_string.split(".") if p)

            if version_tuple(current_hermes_version) < version_tuple(pypi_hermes_version):
                sc.echo(f"You are using an old version of HERMES. ({current_hermes_version})", sc.Formats.WARNING)
                sc.echo(
                    f"Please upgrade to the latest version ({pypi_hermes_version}) before running 'hermes init' to "
                    f"avoid errors!",
                    sc.Formats.FAIL)
            elif version_tuple(current_hermes_version) == version_tuple(pypi_hermes_version):
                sc.echo(f"Your version of HERMES ({current_hermes_version}) is up to date.", sc.Formats.OKGREEN)
            else:
                sc.echo(
                    f"Your version of HERMES ({current_hermes_version}) is even newer than "
                    f"the latest version ({pypi_hermes_version}).", sc.Formats.OKCYAN + sc.Formats.BOLD)
        except Exception as e:
            sc.echo(f"Could not fetch Pypi Hermes version. ({e})", sc.Formats.WARNING)

    def test_initialization(self) -> None:
        """Test if init is possible and wanted. If not: sys.exit()"""
        sc.echo("Preparing HERMES initialization\n")

        # Abort if git is not installed
        if not git_info.is_git_installed():
            sc.echo("Git is currently not installed. It is recommended to use HERMES with git.",
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()

        # Look at the current folder
        self.refresh_folder_info()
        self.hermes_was_already_installed = self.folder_info.has_hermes_toml

        # Abort if there is no git
        if not self.folder_info.has_git_folder:
            sc.echo("The current directory has no `.git` subdirectory. "
                    "Please execute `hermes init` in the root directory of your git project.",
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()

        # Look at git branch & remotes
        self.git_branch = git_info.get_current_branch()
        remotes = git_info.get_remotes()
        if remotes:
            self.git_remote = remotes[0]

        # Let the user choose if there are multiple remotes
        if len(remotes) > 1:
            remote_index = sc.choose(
                "Your git project has multiple remotes. For which remote do you want to setup HERMES?",
                [f"{remote} ({git_info.get_remote_url(remote)})" for remote in remotes]
            )
            self.git_remote = remotes[remote_index]

        # Get url & hoster from remote
        if self.git_remote:
            self.git_remote_url = git_info.get_remote_url(self.git_remote)
            self.git_hoster = get_git_hoster_from_url(self.git_remote_url)

        # Abort with no remote
        else:
            sc.echo("Your git project does not have a remote. It is recommended for HERMES to "
                    "use either GitHub or GitLab as hosting service.", formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()

        # Abort if neither GitHub nor gitlab is used
        if self.git_hoster == GitHoster.Empty:
            project_url = " (" + self.git_remote_url + ")" if self.git_remote_url else ""
            sc.echo("Your git project{} is not connected to GitHub or GitLab. It is recommended for HERMES to "
                    "use one of these hosting services.".format(project_url),
                    formatting=sc.Formats.WARNING)
            self.no_git_setup()
            sys.exit()
        else:
            sc.echo(f"Git project using {self.git_hoster.name} detected.\n")

        # Abort if there is already a hermes.toml
        if self.folder_info.has_hermes_toml:
            sc.echo("The current directory already has a `hermes.toml`. "
                    "It seems like HERMES was already initialized for this project.", formatting=sc.Formats.WARNING)
            if not sc.confirm("Do you want to initialize Hermes anyway? "
                              "(Hermes config files and related project variables will be overwritten.) "):
                sys.exit()

    def create_hermes_toml(self) -> None:
        """Creates the hermes.toml file based on a self.hermes_toml_data"""
        hermes_toml_path = Path("hermes.toml")
        self.mark_as_new_path(hermes_toml_path)
        if (not self.folder_info.has_hermes_toml) \
                or sc.confirm("Do you want to replace your `hermes.toml` with a new one?", default=True):
            with open(hermes_toml_path, 'w') as toml_file:
                # noinspection PyTypeChecker
                toml.dump(self.hermes_toml_data, toml_file)
            sc.echo("`hermes.toml` was created.", formatting=sc.Formats.OKGREEN)

    def create_citation_cff(self) -> None:
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

    def update_gitignore(self) -> None:
        """Creates .gitignore if there is none and adds '.hermes' to it"""
        gitignore_path = Path(".gitignore")
        self.mark_as_new_path(gitignore_path)
        if not self.folder_info.has_gitignore:
            open(gitignore_path, 'w')
            sc.echo("A new `.gitignore` file was created.", formatting=sc.Formats.OKGREEN)
        self.refresh_folder_info()
        if self.folder_info.has_gitignore:
            with open(gitignore_path, "r") as file:
                gitignore_lines = file.readlines()
            if any([line.startswith(".hermes") for line in gitignore_lines]):
                sc.echo("The `.gitignore` file already contains `.hermes/`")
            else:
                with open(gitignore_path, "a") as file:
                    file.write("# Ignoring all HERMES cache files\n")
                    file.write(".hermes/\n")
                    file.write("hermes.log\n")
                sc.echo("Added `.hermes/` to the `.gitignore` file.", formatting=sc.Formats.OKGREEN)

    def get_template_url(self, filename: str) -> str:
        """Returns the full template url with a given filename."""
        return (f"{self.template_base_url}/{self.template_repo}/refs/heads/"
                f"{self.template_branch}/{self.template_folder}/{filename}")

    def create_ci_template(self) -> None:
        """Downloads and configures the ci workflow files using templates from the chosen template branch."""
        match self.git_hoster:
            case GitHoster.GitHub:
                template_url = self.get_template_url("TEMPLATE_hermes_github_to_zenodo.yml")
                ci_file_folder = Path(".github/workflows")
                ci_file_name = "hermes_github.yml"
                ci_file_path = ci_file_folder / ci_file_name
                # Adding paths to our list
                self.mark_as_new_path(Path(".github"))
                self.mark_as_new_path(ci_file_folder)
                self.mark_as_new_path(ci_file_path)
                # Creating folder & ci file
                ci_file_folder.mkdir(parents=True, exist_ok=True)
                sc.debug_info(f"Downloading github template from {template_url}")
                download_file_from_url(template_url, ci_file_path)
                self.configure_ci_template(ci_file_path)
                sc.echo(f"GitHub CI: File was created at {ci_file_path}", formatting=sc.Formats.OKGREEN)
            case GitHoster.GitLab:
                gitlab_ci_template_url = self.get_template_url("TEMPLATE_hermes_gitlab_to_zenodo.yml")
                hermes_ci_template_url = self.get_template_url("hermes-ci.yml")
                gitlab_ci_path = Path(".gitlab-ci.yml")
                gitlab_folder_path = Path("gitlab")
                hermes_ci_path = gitlab_folder_path / "hermes-ci.yml"
                # Adding paths to our list
                self.mark_as_new_path(gitlab_ci_path)
                self.mark_as_new_path(gitlab_folder_path)
                self.mark_as_new_path(hermes_ci_path)
                # Creating the gitlab folder
                gitlab_folder_path.mkdir(parents=True, exist_ok=True)
                # Creating / updating gitlab-ci
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
                # Creating hermes-ci
                download_file_from_url(hermes_ci_template_url, hermes_ci_path)
                self.configure_ci_template(hermes_ci_path)

                # When using gitlab.com we need to use gitlab-org-docker as tag
                if "gitlab.com" in self.git_remote_url:
                    with open(hermes_ci_path, 'r') as file:
                        content = file.read()
                    new_content = re.sub(r'(tags:\n\s+- )docker', r'\1gitlab-org-docker', content)
                    with open(hermes_ci_path, 'w') as file:
                        file.write(new_content)

                sc.echo(f"GitLab CI: {hermes_ci_path} was created.", formatting=sc.Formats.OKGREEN)

    def configure_ci_template(self, ci_file_path) -> None:
        """Replaces all {%parameter%} in a ci file with values from ci_parameters dict"""
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(""),
                                       block_start_string="{%%", block_end_string="%%}",
                                       variable_start_string="{%", variable_end_string="%}")
        source_text = Path(ci_file_path).read_text(encoding="utf-8")
        used_params = jinja2.meta.find_undeclared_variables(jinja_env.parse(source_text))
        template = jinja_env.get_template(str(ci_file_path))
        missing = [p for p in used_params if p not in self.ci_parameters]
        if missing:
            sc.echo("CI Template has missing parameters: {missing}", formatting=sc.Formats.WARNING)
        rendered = template.render(self.ci_parameters)
        with open(ci_file_path, 'w') as file:
            file.write(rendered)

    def create_zenodo_token(self) -> None:
        """Makes the user create a zenodo token and saves it in self.deposit_platform.token."""
        # Deactivated Zenodo OAuth as long as the refresh token bug is not fixed.
        if self.setup_method == "a":
            sc.echo("Doing OAuth with Zenodo is currently not available.")
        if self.setup_method == "m" or self.deposit_platform.token == '':
            zenodo_token_url = urljoin(self.deposit_platform.url,
                                       "account/settings/applications/tokens/new/")
            sc.echo("{} and create an access token.".format(
                sc.create_console_hyperlink(zenodo_token_url, "Open this link")
            ))
            sc.echo("It needs the scopes \"deposit:actions\" and \"deposit:write\".")
            if self.setup_method == "m":
                sc.press_enter_to_continue()
            else:
                while True:
                    self.deposit_platform.token = sc.answer("Enter the token here: ")
                    valid = connect_zenodo.test_if_token_is_valid(self.deposit_platform.token)
                    if valid:
                        sc.echo(f"The token was validated by {self.deposit_platform.name}.",
                                formatting=sc.Formats.OKGREEN)
                        break
                    else:
                        sc.echo(f"The token could not be validated by {self.deposit_platform.name}. "
                                "Make sure to enter the complete token.\n"
                                "(If this error persists, you should restart and switch to the manual setup mode.)",
                                formatting=sc.Formats.WARNING)

    def create_rodare_token(self):
        token_url = urljoin(self.deposit_platform.url, "account/settings/applications/tokens/new/")
        sc.echo("{} and create an access token.".format(
            sc.create_console_hyperlink(token_url, "Open this link")
        ))
        sc.echo("It needs the scopes \"deposit:actions\" and \"deposit:write\".")
        if self.setup_method == "m":
            sc.press_enter_to_continue()
        else:
            # TODO try to validate the token
            self.deposit_platform.token = sc.answer("Enter the token here: ")

    def configure_git_project(self) -> None:
        """Adds the token to the git secrets & changes action workflow settings."""
        match self.git_hoster:
            case GitHoster.GitHub:
                self.configure_github()
            case GitHoster.GitLab:
                self.configure_gitlab()

    def configure_github(self) -> None:
        oauth_success = False
        if self.setup_method == "a":
            self.tokens[GitHoster.GitHub] = connect_github.get_access_token()
            if self.tokens[GitHoster.GitHub]:
                sc.echo("OAuth at GitHub was successful.", formatting=sc.Formats.OKGREEN)
                sc.debug_info(github_token=self.tokens[GitHoster.GitHub])
                connect_github.create_secret(self.git_remote_url, self.deposit_platform.token_name,
                                             secret_value=self.deposit_platform.token,
                                             token=self.tokens[GitHoster.GitHub])
                connect_github.allow_actions(self.git_remote_url,
                                             token=self.tokens[GitHoster.GitHub])
                oauth_success = True
            else:
                sc.echo("Something went wrong while doing OAuth. You'll have to do it manually instead.",
                        formatting=sc.Formats.WARNING)
        if not oauth_success:
            sc.echo("Add the {} token{} to your {} under the name {}.".format(
                self.deposit_platform.name,
                f" ({self.deposit_platform.token})" if self.deposit_platform.token else "",
                sc.create_console_hyperlink(
                    self.git_remote_url + "/settings/secrets/actions",
                    "project's GitHub secrets"
                ),
                self.deposit_platform.token_name
            ))
            sc.press_enter_to_continue()
            sc.echo("Next open your {} and check the checkbox which reads:".format(
                sc.create_console_hyperlink(
                    self.git_remote_url + "/settings/actions", "project settings"
                )
            ))
            sc.echo("Allow GitHub Actions to create and approve pull requests")
            sc.press_enter_to_continue()

    def configure_gitlab(self) -> None:
        # Doing it with API / OAuth
        oauth_success = False
        if self.setup_method == "a":
            gl = connect_gitlab.GitLabConnection(self.git_remote_url)
            token = ""
            if not gl.has_client():
                sc.echo("Unfortunately HERMES does not support automatic authorization with your GitLab "
                        "installment.")
                sc.echo("Go to your {} and create a new token.".format(
                    sc.create_console_hyperlink(
                        self.git_remote_url + "/-/settings/access_tokens",
                        "project's access tokens")
                ))
                sc.echo("It needs to have the 'developer' role and 'api' + 'write_repository' scope.")
                token = sc.answer("Then paste the token here: ")
            if gl.authorize(token):
                vars_created = gl.create_variable(
                    self.deposit_platform.token_name, self.deposit_platform.token,
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
                    self.git_remote_url + "/-/settings/access_tokens", "project's access tokens")
            ))
            sc.echo("It needs to have the 'developer' role and 'write_repository' scope.")
            sc.press_enter_to_continue()
            sc.echo("Open your {} and go to 'Variables'".format(
                sc.create_console_hyperlink(
                    self.git_remote_url + "/-/settings/ci_cd", "project's ci settings")
            ))
            sc.echo("Then, add that token as variable with key HERMES_PUSH_TOKEN.")
            sc.echo("(For your safety, you should set the visibility to 'Masked and hidden'.)")
            sc.press_enter_to_continue()
            sc.echo("Next, add the {} token{} as variable with key {}.".format(
                self.deposit_platform.name,
                f" ({self.deposit_platform.token})" if self.deposit_platform.token else "",
                self.deposit_platform.token_name
            ))
            sc.echo("(For your safety, you should set the visibility to 'Masked and hidden'.)")
            sc.press_enter_to_continue()

    def choose_deposit_platform(self) -> None:
        """User chooses his desired deposit platform."""
        deposit_platform_index = sc.choose(
            "Where do you want to publish the software?", [do.name for do in DepositOptions]
        )
        self.deposit_platform = DepositOptions[deposit_platform_index]

    def integrate_deposit_platform(self) -> None:
        """Makes changes to the toml data or something else based on the chosen deposit platform."""
        deposit_plugin: str = self.deposit_platform.plugin_name
        self.hermes_toml_data["deposit"]["target"] = deposit_plugin
        self.hermes_toml_data["deposit"][deposit_plugin] = {}
        self.hermes_toml_data["deposit"][deposit_plugin]["site_url"] = self.deposit_platform.url
        self.ci_parameters["deposit_parameter_token"] = f"-O {deposit_plugin}.auth_token"
        self.ci_parameters["deposit_token_name"] = self.deposit_platform.token_name

        if deposit_plugin.startswith("invenio") or deposit_plugin.startswith("rodare"):
            # Invenio & rodare need access_right
            # For possible customization we ask the user here
            options = ["open", "closed", "restricted", "embargoed"]
            target_access_right_index = sc.choose(
                text="Select an access right for your publication",
                options=options
            )
            target_access_right = options[target_access_right_index]
            self.hermes_toml_data["deposit"][deposit_plugin]["access_right"] = target_access_right
            if target_access_right == "restricted":
                conditions = sc.answer("Enter the access conditions of the restriction: ")
                self.hermes_toml_data["deposit"][deposit_plugin]["access_conditions"] = conditions
            elif target_access_right == "embargoed":
                embargo_date = sc.answer("Enter the embargo date (YYYY-MM-DD): ")
                self.hermes_toml_data["deposit"][deposit_plugin]["embargo_date"] = embargo_date

        if deposit_plugin.startswith("rodare"):
            # Rodare needs the robis_pub_id
            robis_pub_id = sc.answer("Enter the corresponding Robis Publication ID: ")
            self.hermes_toml_data["deposit"][deposit_plugin]["robis_pub_id"] = robis_pub_id

    def choose_setup_method(self) -> None:
        """User chooses his desired setup method: Either preferring automatic (if available) or manual."""
        setup_method_index = sc.choose(
            f"How do you want to connect {self.deposit_platform.name} "
            f"with your {self.git_hoster.name} CI?",
            options=[
                "Automatically (using OAuth / Device Flow)",
                "Manually (with instructions)",
            ]
        )
        self.setup_method = ["a", "m"][setup_method_index]

    def connect_deposit_platform(self) -> None:
        """Acquires the access token of the chosen deposit platform."""
        used_deposit_plugin = self.deposit_platform.plugin_name
        deposit_url = self.deposit_platform
        deposit_name = self.deposit_platform.name
        if used_deposit_plugin.startswith("invenio"):
            connect_zenodo.setup(zenodo_url=self.deposit_platform.url, display_name=self.deposit_platform.name)
            self.create_zenodo_token()
        elif used_deposit_plugin.startswith("rodare"):
            self.create_rodare_token()
        else:
            sc.echo(f"Unknown deposit plugin: {used_deposit_plugin}", formatting=sc.Formats.WARNING)
            sc.echo(f"Getting an access token from {deposit_name} ({deposit_url}) is not supported by hermes init."
                    "You might have to do it manually instead.", formatting=sc.Formats.WARNING)

    def choose_plugins(self) -> None:
        """User chooses the plugins he wants to use."""
        plugin_infos: list[marketplace.PluginInfo] = marketplace.get_plugin_infos()
        plugins_builtin: list[marketplace.PluginInfo] = list(filter(lambda p: p.builtin, plugin_infos))
        plugins_available: list[marketplace.PluginInfo] = list(filter(lambda p: not p.builtin, plugin_infos))
        plugins_selected: list[marketplace.PluginInfo] = []
        sc.echo("The following plugins are already builtin:")
        for info in plugins_builtin:
            sc.echo(str(info), formatting=sc.Formats.OKGREEN)
        sc.echo("")
        while True:
            if plugins_selected:
                sc.echo("The following plugins are going to be installed:")
                for info in plugins_selected:
                    sc.echo(str(info), formatting=sc.Formats.OKCYAN)
                sc.echo("")
            if plugins_available:
                sc.echo("The following plugins are available for installation:")
                for info in plugins_available:
                    sc.echo(str(info), formatting=sc.Formats.WARNING, no_log=True)
                    if info.abstract:
                        sc.echo("-> " + info.abstract, formatting=sc.Formats.ITALIC+sc.Formats.WARNING, no_log=True)
                sc.echo("")
            else:
                self.selected_plugins = plugins_selected
                break
            no_text = "No further plugins needed"
            choice = sc.choose("Do you want to add a plugin?",
                               [no_text] + [f"Add {p.name}" for p in plugins_available])
            if choice == 0:
                self.selected_plugins = plugins_selected
                break
            else:
                chosen_plugin = plugins_available.pop(choice - 1)
                plugins_selected.append(chosen_plugin)

    def integrate_plugins(self) -> None:
        """
        Plugin installation is added to the ci-parameters.
        Also for now we use this method to do custom plugin installation steps.
        """
        for plugin_info in self.selected_plugins:
            if not plugin_info.is_valid():
                sc.echo(f"Could not install plugin: {plugin_info.name}", formatting=sc.Formats.FAIL)
                continue
            pip_install = plugin_info.get_pip_install_command()
            self.ci_parameters["pip_install_plugins_github"] = \
                self.ci_parameters.get("pip_install_plugins_github", "") + "      - run: " + pip_install + "\n"
            self.ci_parameters["pip_install_plugins_gitlab"] = \
                self.ci_parameters.get("pip_install_plugins_gitlab", "") + "    - " + pip_install + "\n"
            match plugin_info.name:
                case "hermes-plugin-python":
                    self.hermes_toml_data["harvest"]["sources"].append("toml")
                case "hermes-plugin-git":
                    self.hermes_toml_data["harvest"]["sources"].append("git")

    def no_git_setup(self, start_question: str = "") -> None:
        """Makes the init for a gitless project (basically just creating hermes.toml)"""
        if start_question == "":
            start_question = ("Do you want to initialize HERMES anyways? (CI/CD files for automated publishing will "
                              "NOT be created)")
        if sc.confirm(start_question):
            sc.max_steps = 2

            sc.next_step("Create hermes.toml file")
            self.create_hermes_toml()

            sc.next_step("Create CITATION.cff file")
            self.create_citation_cff()

            self.clean_up_files(False)
            sc.echo("\nHERMES is now initialized (without git integration or CI/CD files).\n",
                    formatting=sc.Formats.OKGREEN)

    def choose_push_trigger(self) -> None:
        """User chooses the branch / tag that should be used to trigger the whole hermes pipeline."""
        push_choice = sc.choose(
            "When should the automated HERMES process start?",
            [
                "When I push on target branch",
                f"When I push on current branch ({self.git_branch})",
                "When I push any tag",
                "When I push a tag with target pattern"
            ]
        )
        if push_choice == 0:
            branch_suggestion_max_count = 9
            branch_suggestions: list[str] = git_info.run_git_command(
                "for-each-ref --sort=-committerdate refs/heads/ --format='%(refname:short)'"
            ).split("\n")
            branch_suggestions = [b.strip() for b in branch_suggestions if b.strip() != ""]
            branch_suggestions.sort()
            branch_suggestions.sort(key=lambda branch_name: len(branch_name))
            branch_suggestions = branch_suggestions[:branch_suggestion_max_count]
            branch_count = len(branch_suggestions)
            branch_suggestions.append("Custom branch name")
            branch_choice = sc.choose("Choose target branch: ", branch_suggestions)
            if branch_choice < branch_count:
                self.set_push_trigger_to_branch(branch_suggestions[branch_choice].removeprefix("'").removesuffix("'"))
            else:
                branch = sc.answer("Enter custom branch name: ")
                self.set_push_trigger_to_branch(branch)
        elif push_choice == 1:
            self.set_push_trigger_to_branch(self.git_branch)
        elif push_choice == 2:
            self.set_push_trigger_to_tag()
        elif push_choice == 3:
            pattern_hint = ""
            if self.git_hoster == GitHoster.GitHub:
                pattern_hint = " (GitHub uses glob patterns)"
            elif self.git_hoster == GitHoster.GitLab:
                pattern_hint = " (Gitlab uses regex)"
            pattern = sc.answer(f"Enter the target tag-pattern{pattern_hint}: ")
            self.set_push_trigger_to_tag(pattern)

    def set_push_trigger_to_branch(self, branch: str) -> None:
        """Sets the CI parameters, so that the pipeline gets triggered when the branch gets pushed."""
        self.ci_parameters["gh_push_branches_or_tags"] = "branches"
        self.ci_parameters["gh_push_target"] = branch
        self.ci_parameters["gl_push_condition"] = f"$CI_COMMIT_BRANCH == \"{branch}\""
        bold_branch = sc.Formats.BOLD.wrap_around(branch)
        sc.echo(f"The HERMES pipeline will be activated when you push on {bold_branch}.",
                formatting=sc.Formats.OKGREEN)
        sc.echo()

    def set_push_trigger_to_tag(self, tag_pattern: str = "") -> None:
        """
        Sets the CI parameters, so that the pipeline gets triggered when a tag that matches the pattern gets pushed.
        """
        self.ci_parameters["gh_push_branches_or_tags"] = "tags"
        self.ci_parameters["git_create_curate_branch"] = 'git checkout -b "hermes/curate-$SHORT_SHA" ${{ github.ref }}'
        if tag_pattern:
            self.ci_parameters["gh_push_target"] = f"\"{tag_pattern}\""
            self.ci_parameters["gl_push_condition"] = f"$CI_COMMIT_TAG =~ {tag_pattern}"
            bold_pattern = sc.Formats.BOLD.wrap_around(tag_pattern)
            sc.echo(f"The HERMES pipeline will be activated when you push a tag that fits '{bold_pattern}'.",
                    formatting=sc.Formats.OKGREEN)
        else:
            self.ci_parameters["gh_push_target"] = "\"*\""
            self.ci_parameters["gl_push_condition"] = "$CI_COMMIT_TAG"
            sc.echo("The HERMES pipeline will be activated when you push a tag.", formatting=sc.Formats.OKGREEN)
        sc.echo()

    def choose_deposit_files(self) -> None:
        """User chooses the files that should be included in the deposition."""
        dp_name = self.deposit_platform.name
        add_readme = False
        if self.folder_info.has_readme:
            if sc.confirm(f"Do you want to append your README.md to the {dp_name} upload?"):
                self.ci_parameters["deposit_extra_files"] = "--file README.md "
                add_readme = True
            else:
                self.ci_parameters["deposit_extra_files"] = ""
                add_readme = False
        options = [
            "Nothing else",
            "All (visible) folders",
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
            case 0:  # Nothing
                self.ci_parameters["deposit_zip_files"] = "-"
            case 1:  # All folders
                self.ci_parameters["deposit_zip_files"] = " ".join(self.folder_info.dir_folders)
            case 2:  # All folders all files
                self.ci_parameters["deposit_zip_files"] = ""
            case 3:  # Custom List
                custom_files = []
                while True:
                    custom_path = sc.answer("Enter a path you want to include (enter nothing if you are done): ")
                    if custom_path.strip() == "":
                        break
                    if os.path.exists(os.path.join(self.folder_info.current_dir, custom_path)):
                        custom_files.append(custom_path)
                        sc.echo(f"{custom_path} has been added.", formatting=sc.Formats.OKGREEN)
                    else:
                        sc.echo(f"{custom_path} does not exist.", formatting=sc.Formats.FAIL)
                if custom_files:
                    self.ci_parameters["deposit_zip_files"] = " ".join(custom_files)
                else:
                    self.ci_parameters["deposit_zip_files"] = "-"
            case _:
                index = int(file_choice) - folder_base_index
                if 0 <= index < len(self.folder_info.dir_folders):
                    self.ci_parameters["deposit_zip_files"] = self.folder_info.dir_folders[index]
        sc.echo("Your upload will consist of the following:")
        if add_readme:
            sc.echo("\tUnzipped:", formatting=sc.Formats.BOLD)
            sc.echo("\t\tREADME.md", formatting=sc.Formats.OKCYAN)
        sc.echo("\tZipped:", formatting=sc.Formats.BOLD)
        if self.ci_parameters["deposit_zip_files"] == "-":
            sc.echo("\t\t-", formatting=sc.Formats.OKCYAN)
        elif self.ci_parameters["deposit_zip_files"] == "":
            for file in self.folder_info.dir_list:
                sc.echo(f"\t\t{file}", formatting=sc.Formats.OKCYAN)
        else:
            for file in self.ci_parameters["deposit_zip_files"].split(" "):
                sc.echo(f"\t\t{file}", formatting=sc.Formats.OKCYAN)
        if not sc.confirm("Do you want to confirm your selection?"):
            sc.echo("Your selection was cleared. Now you can select the files again.")
            self.choose_deposit_files()
        else:
            sc.echo("You can change the selected files later inside the CI file or by running 'hermes init' again.")

    def mark_as_new_path(self, path: Path, avoid_existing: bool = True) -> None:
        """
        This method should be called directly BEFORE creating a new file in the given Path.
        This way we can look if something already exists there to decide later-on if we want to delete it on abort.
        """
        if (not avoid_existing) or (not path.exists()):
            self.new_created_paths.append(path)

    def clean_up_files(self, aborted: bool) -> None:
        """
        This gets called when init is finished (successfully or aborted).
        It cleans up unwanted files (like .hermes folder) and everything new when aborted.
        """
        sc.echo("Cleaning unused files...")
        hidden_hermes_path = Path(".hermes")
        if hidden_hermes_path.exists() and hidden_hermes_path.is_dir():
            shutil.rmtree(hidden_hermes_path)
        if aborted:
            if not self.hermes_was_already_installed:
                for path in reversed(self.new_created_paths):
                    try:
                        if path.is_dir():
                            path.rmdir()
                        else:
                            os.remove(path)
                    except Exception as e:
                        sc.echo(f"Cleaning Warning: Could not remove {path}. ({e})")
