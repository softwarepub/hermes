# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import argparse
import json
import logging
from datetime import datetime
import typing as t
from typing import Optional, Dict, Tuple

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
    """Harvest metadata from the provided URL or configured sources."""

    command_name = "harvest"
    settings_class = HarvestSettings

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Adds arguments for the harvest command to harvest metadata from the specific URL."""
        parser.add_argument('url', nargs='?', default=None, help="Optional URL to harvest from")

    def __call__(self, args: argparse.Namespace) -> None:
        """Execute the harvesting command based on the provided arguments."""
        self.args = args
        ctx = HermesContext()
        ctx.init_cache("harvest")

        if hasattr(args, 'url') and args.url:
            result = self._process_url(args.url, ctx)
            if result is None:
                logger.error("Failed to process URL: %s", args.url)
        else:
            self._harvest_locally(ctx)

    def _process_url(self, url: str, ctx: HermesContext) -> Optional[Dict[str, Dict]]:
        """Process the provided URL for metadata harvesting."""
        try:
            files_to_search = [CITATION_FILE, CODEMETA_FILE]
            found_files = self._search_repo_for_metadata(url, files_to_search)

            if not found_files:
                raise FileNotFoundError("Neither CITATION.cff nor codemeta.json found in the repository.")

            cff_dict = self._handle_citation_file(found_files)
            codemeta_dict = self._handle_codemeta_file(found_files)

            logger.info("Harvesting successful from URL: %s", url)
            print('**********************************************************')
            print("Original CodeMeta from codemeta.json:")
            print(json.dumps(codemeta_dict, indent=4))

            print('**********************************************************')
            print("CFF converted to CodeMeta:")
            print(json.dumps(cff_dict, indent=4))

            return {
                "codemeta_from_cff": cff_dict,
                "codemeta_json": codemeta_dict
            }

        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Error processing URL: {e}")
            return None

    def _harvest_locally(self, ctx: HermesContext) -> None:
        """Harvest metadata from configured sources."""
        for plugin_name in self.settings.sources:
            try:
                plugin_func = self.plugins[plugin_name]()
                harvested_data, tags = plugin_func(self)

                with HermesHarvestContext(ctx, plugin_name) as harvest_ctx:
                    harvest_ctx.update_from(harvested_data,
                                            plugin=plugin_name,
                                            timestamp=datetime.now().isoformat(), **tags)
                    for _key, ((_value, _tag), *_trace) in harvest_ctx._data.items():
                        if any(v != _value and t == _tag for v, t in _trace):
                            raise MergeError(_key, None, _value)

            except KeyError as e:
                self.log.error("Plugin '%s' not found.", plugin_name)
                self.errors.append(e)

            except HermesValidationError as e:
                self.log.error("Error while executing %s: %s", plugin_name, e)
                self.errors.append(e)

    def _search_repo_for_metadata(self, repo_url: str, files_to_search: list) -> Dict[str, str]:
        """Search for metadata files in the given GitHub repository and return their URLs."""
        repo_api_url = repo_url.rstrip('/').replace('https://github.com/', 'https://api.github.com/repos/') + '/contents'

        try:
            response = requests.get(repo_api_url)
            response.raise_for_status()

            repo_files = response.json()
            found_files = {file_entry["name"]: file_entry["download_url"] for file_entry in repo_files
                           if file_entry["name"] in files_to_search}

            return found_files

        except requests.RequestException as e:
            if e.response and e.response.status_code == 404:
                logger.error(f"Repository not found: {repo_url}")
                raise FileNotFoundError(f"Repository {repo_url} not found or is private.")
            else:
                logger.error(f"Failed to list repository contents: {e}")
                raise

    def _fetch_file_from_url(self, file_url: str) -> str:
        """Fetch the content of a file from its URL."""
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch file from {file_url}: {e}")
            raise FileNotFoundError(f"Unable to fetch file from {file_url}")

    def _load_cff_from_file(self, cff_data: str) -> dict:
        """Load and parse CFF data from a file."""
        yaml = YAML(typ='safe')
        yaml.constructor.yaml_constructors[u'tag:yaml.org,2002:timestamp'] = yaml.constructor.yaml_constructors[
            u'tag:yaml.org,2002:str']
        return yaml.load(cff_data)

    def _convert_cff_to_codemeta(self, cff_data: str) -> dict:
        """Convert metadata from CFF to CodeMeta format."""
        codemeta_str = Citation(cff_data).as_codemeta()
        return json.loads(codemeta_str)

    def _patch_author_emails(self, cff: dict, codemeta: dict) -> dict:
        """Patch author emails from CFF into CodeMeta."""
        cff_authors = cff["authors"]
        for i, author in enumerate(cff_authors):
            if "email" in author:
                codemeta["author"][i]["email"] = author["email"]
        return codemeta

    def _handle_citation_file(self, found_files: dict) -> Optional[dict]:
        """Handle the CITATION.cff file if found."""
        if CITATION_FILE in found_files:
            cff_content = self._fetch_file_from_url(found_files[CITATION_FILE])
            cff_dict = self._load_cff_from_file(cff_content)
            return self._convert_cff_to_codemeta(cff_content)
        return None

    def _handle_codemeta_file(self, found_files: dict) -> Optional[dict]:
        """Handle the codemeta.json file if found."""
        if CODEMETA_FILE in found_files:
            codemeta_content = self._fetch_file_from_url(found_files[CODEMETA_FILE])
            return json.loads(codemeta_content)
        return None