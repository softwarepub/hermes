# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import json
import logging
from datetime import datetime
import typing as t
from typing import Optional, Dict, Tuple, List
import yaml
from urllib.parse import quote

import requests
from pydantic import BaseModel
from ruamel.yaml import YAML
from cffconvert import Citation

from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.context import HermesContext, HermesHarvestContext
from hermes.model.errors import HermesValidationError, MergeError

CITATION_FILE = "CITATION.cff"
CODEMETA_FILE = "codemeta.json"

logger = logging.getLogger(__name__)

class HermesHarvestPlugin(HermesPlugin):
    """Base plugin that does harvesting.

    TODO: describe the harvesting process and how this is mapped to this plugin.
    """

    def __call__(self, command: HermesCommand) -> t.Tuple[t.Dict, t.Dict]:
        pass


class HarvestSettings(BaseModel):
    """Generic harvesting settings."""

    sources: list[str] = []


class HermesHarvestCommand(HermesCommand):
    """ Harvest metadata from configured sources. """

    command_name = "harvest"
    settings_class = HarvestSettings
    
    def __call__(self, args) -> None:
        self.args = args
        ctx = HermesContext()
        ctx.init_cache("harvest")
        
        if args.url:
            self._process_url(args.url, ctx)
        else:
            self._harvest_locally(ctx)

    def _process_url(self, url: str, ctx: HermesContext) -> Optional[Tuple[Dict, Dict]]:
        """Process the provided URL for metadata harvesting."""
        try:
            files_to_search = [CITATION_FILE, CODEMETA_FILE]
            if "github.com" in url:
                found_files = self._search_github_repo_for_metadata(url, files_to_search)
            elif "gitlab.com" in url:
                found_files = self._search_gitlab_repo_for_metadata(url, files_to_search)
            else:
                raise ValueError("Unsupported repository provider. Only GitHub and GitLab are supported.")
            if not found_files:
                raise FileNotFoundError(f"Neither {CITATION_FILE} nor {CODEMETA_FILE} found in repository.")
            # Process and store metadata from files
            self._process_found_files(found_files, ctx)
            return None, None
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Error processing URL: {e}")
            return None, None
        
    def _search_github_repo_for_metadata(self, repo_url: str, files_to_search: List[str]) -> Dict[str, str]:
        """Search for metadata files in a GitHub repository."""
        repo_api_url = f"{repo_url.rstrip('/').replace('https://github.com/', 'https://api.github.com/repos/')}/contents"
        try:
            response = requests.get(repo_api_url)
            response.raise_for_status()
            repo_files = response.json()
            return {file["name"]: file["download_url"] for file in repo_files if file["name"] in files_to_search}
        except requests.HTTPError as e:
            logger.error(f"HTTP Error accessing GitHub repository: {repo_url}, {e}")
            raise FileNotFoundError(f"GitHub repository {repo_url} not found or is private.")
        except requests.RequestException as e:
            logger.error(f"Failed to list GitHub repository contents: {e}")
            raise

    def _search_gitlab_repo_for_metadata(self, repo_url: str, files_to_search: List[str]) -> Dict[str, str]:
        """Search for metadata files in a GitLab repository."""
        try:
            project_path = repo_url.rstrip('/').split('gitlab.com/')[1]
            encoded_project = quote(project_path, safe='')
            found_files = {}
            for file_name in files_to_search:
                file_api_url = f"https://gitlab.com/api/v4/projects/{encoded_project}/repository/files/{quote(file_name)}/raw?ref=main"
                
                response = requests.get(file_api_url)
                if response.status_code == 200:
                    found_files[file_name] = file_api_url
                elif response.status_code != 404:
                    logger.error(f"Error accessing GitLab repository: {repo_url}, {response.status_code}")
                    raise FileNotFoundError(f"GitLab repository {repo_url} not found or is private.")
            return found_files
        except requests.RequestException as e:
            logger.error(f"Failed to list GitLab repository contents: {e}")
            raise
            
    def _harvest_locally(self, ctx: HermesContext) -> None:
        """Harvest metadata from configured sources using plugins."""
        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]()
                harvested_data, tags = plugin_func(self)
                self.store_harvested_data(ctx, harvested_data, tags, plugin_name)
            except KeyError as e:
                logger.error(f"Plugin '{plugin_name}' not found. Error: {e}")
            except HermesValidationError as e:
                logger.error(f"Error while executing '{plugin_name}': {e}")

    def _search_repo_for_metadata(self, repo_url: str, files_to_search: List[str]) -> Dict[str, str]:
        """Search for metadata files in the given GitHub repository and return their URLs."""
        repo_api_url = f"{repo_url.rstrip('/').replace('https://github.com/', 'https://api.github.com/repos/')}/contents"
        try:
            response = requests.get(repo_api_url)
            response.raise_for_status()
            repo_files = response.json()
            return {file["name"]: file["download_url"] for file in repo_files if file["name"] in files_to_search}
        except requests.HTTPError as e:
            logger.error(f"HTTP Error accessing repository: {repo_url}, {e}")
            raise FileNotFoundError(f"Repository {repo_url} not found or is private.")
        except requests.RequestException as e:
            logger.error(f"Failed to list repository contents: {e}")
            raise

    def _process_found_files(self, found_files: Dict[str, str], ctx: HermesContext) -> None:
        """Process and store metadata from CFF and CodeMeta files."""
        cff_data = self._handle_citation_file(found_files)
        codemeta_data = self._handle_codemeta_file(found_files)
        if cff_data:
            self.store_harvested_data(ctx, cff_data, {"source_type": "CFF"}, "cff")
        if codemeta_data:
            self.store_harvested_data(ctx, codemeta_data, {"source_type": "CodeMeta"}, "codemeta")

    def _fetch_file_from_url(self, file_url: str) -> str:
        """Fetch the content of a file from its URL."""
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch file from {file_url}: {e}")
            raise FileNotFoundError(f"Unable to fetch file from {file_url}")
        
    def _patch_author_emails(self, cff: dict, codemeta: dict) -> dict:
        cff_authors = cff["authors"]
        for i, author in enumerate(cff_authors):
            if "email" in author:
                codemeta["author"][i]["email"] = author["email"]
        return codemeta

    def _handle_citation_file(self, found_files: Dict[str, str]) -> Optional[Dict]:
        """Handle the CITATION.cff file if found."""
        if CITATION_FILE in found_files:
            cff_content_str = self._fetch_file_from_url(found_files[CITATION_FILE])
            cff_content = yaml.safe_load(cff_content_str)
            cff_codemeta_dict = self._convert_cff_to_codemeta(cff_content_str)
            cff_codemeta_dict = self._patch_author_emails(cff_content, cff_codemeta_dict)
            return cff_codemeta_dict
        return None

    def _handle_codemeta_file(self, found_files: Dict[str, str]) -> Optional[Dict]:
        """Handle the codemeta.json file if found."""
        if CODEMETA_FILE in found_files:
            codemeta_content = self._fetch_file_from_url(found_files[CODEMETA_FILE])
            return json.loads(codemeta_content)
        return None

    def _convert_cff_to_codemeta(self, cff_data: str) -> Dict:
        """Convert metadata from CFF to CodeMeta format."""
        codemeta_str = Citation(cff_data).as_codemeta()
        return json.loads(codemeta_str)

    def store_harvested_data(self, ctx: HermesContext, harvested_data: Dict, tags: Dict, source_name: str) -> None:
        """Store harvested data into Hermes context."""
        with HermesHarvestContext(ctx, source_name) as harvest_ctx:
            harvest_ctx.update_from(harvested_data, plugin=source_name, timestamp=datetime.now().isoformat(), **tags)
            self._check_for_merge_conflicts(harvest_ctx)

    def _check_for_merge_conflicts(self, harvest_ctx: HermesHarvestContext) -> None:
        """Check for merge conflicts after updating harvest context."""
        for key, ((value, tag), *trace) in harvest_ctx._data.items():
            if any(v != value and t == tag for v, t in trace):
                raise MergeError(key, None, value)
