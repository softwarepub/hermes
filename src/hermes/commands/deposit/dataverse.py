# SPDX-FileCopyrightText: 2025 Forschungszentrum Jülich GmbH
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: Nitai Heeb

import json
import logging
from pathlib import Path

import requests
from easyDataverse import Dataset, Dataverse, License
from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin
from hermes.commands.deposit.error import DepositionUnauthorizedError
from hermes.model.path import ContextPath
from hermes.utils import hermes_doi

_log = logging.getLogger("cli.deposit.dataverse")


class DataverseDepositSettings(BaseModel):
    """Settings required to deposit into Dataverse."""
    site_url: str = ""
    target_collection: str = ""
    api_token: str = ""
    target_pid: str = None
    publication_type: str = "software"
    files: list[Path] = []


class DataverseDepositPlugin(BaseDepositPlugin):
    platform_name = "dataverse"
    settings_class = DataverseDepositSettings

    def __init__(self, command, ctx) -> None:
        """
        Sets up the DataverseDepositPlugin with data from the hermes toml.
        Tests if everything is valid and creates an easyDataverse client.
        """
        super().__init__(command, ctx)
        self.config = getattr(self.command.settings, self.platform_name)
        self.check_if_all_valid()
        self.client = Dataverse(server_url=self.config.site_url, api_token=self.config.api_token)
        self.ctx_path = ContextPath.parse(f"deposit.{self.platform_name}")

    def check_if_all_valid(self) -> None:
        """
        Tests if all conditions are met before starting the rest of the deposit.
        """
        self.check_version()
        self.check_api_token()
        self.check_target_collection()
        self.check_target_pid()
        self.check_publication_type()

    def check_version(self) -> None:
        """
        Tests if the site_url is reachable as dataverse instance.
        Also saves the dataverse version in the context incase we want to use it later on.
        """
        url = f"{self.config.site_url}/api/info/version"
        res = requests.get(url)
        if not res.ok:
            raise RuntimeError(f"Dataverse ({self.config.site_url}) not reachable.")
        version_info = res.json().get("data", {}).get("version", "")
        self.ctx.update(self.ctx_path["dataverse_version"], version_info)

    def check_api_token(self) -> None:
        api_token = self.config.api_token
        if not api_token:
            raise DepositionUnauthorizedError("No api-token given for deposition platform (dataverse).")
        token_valid_url = f"{self.config.site_url}/api/users/token"
        token_valid_response = requests.get(token_valid_url, headers={"X-Dataverse-key": api_token})
        if not token_valid_response.ok:
            raise DepositionUnauthorizedError("Given api-token for deposition platform (dataverse) is not valid.")

    def check_target_collection(self) -> None:
        """
        Tests if the target collection exists.
        """
        target_collection = self.config.target_collection
        url = f"{self.config.site_url}/api/dataverses/{target_collection}"
        res = requests.get(url)
        if not res.ok:
            raise RuntimeError(f"Dataverse collection '{target_collection}' not found.")

    def check_target_pid(self) -> None:
        """
        Tests if the given pid is valid.
        """
        if not self.config.target_pid:
            return
        url = f"{self.config.site_url}/api/datasets/:persistentId/?persistentId={self.config.target_pid}"
        res = requests.get(url)
        if not res.ok:
            raise RuntimeError(f"Dataset {self.config.target_pid} not found.")
        data = res.json().get("data", {})
        if self.config.target_collection and not data.get("ownerAlias") == self.config.target_collection:
            _log.warning("Dataset is not located inside the target collection.")

    def check_publication_type(self) -> None:
        """
        Tests if the given publication type (most likely "software") is supported by the target dataverse.
        """
        url = f"{self.config.site_url}/api/datasets/datasetTypes"
        res = requests.get(url)
        if res.ok:
            types = res.json().get("data", [])
            type_names = [t["name"] for t in types]
            if self.config.publication_type not in type_names:
                raise RuntimeError(
                    f"Publication type '{self.config.publication_type}' not supported on target Dataverse.")
        else:
            # TBD what to do when showing supported datasetTypes does not work?
            # This is currently the case for https://data.fz-juelich.de/ & https://data-beta.fz-juelich.de/
            pass

    def map_metadata(self) -> None:
        """
        Saves the given codemeta-metadata, so it's ready to be used.
        Since we add the metadata with easyDataverse there is no mapping needed at this point.
        """
        metadata = self.ctx["codemeta"]
        self.ctx.update(self.ctx_path["depositionMetadata"], metadata)
        with open(self.ctx.get_cache("deposit", self.platform_name, create=True), 'w') as f:
            json.dump(metadata, f, indent=2)

    def is_initial_publication(self) -> bool:
        return self.config.target_pid is None

    def update_metadata_on_dataset(self, dataset: Dataset) -> None:
        """
        Sets metadata on an easyDataverse.Dataset using the depositionMetadata
        """
        metadata = self.ctx[self.ctx_path["depositionMetadata"]]
        dataset.citation.title = metadata.get("name", "")
        dataset.citation.subject = ["Other"]
        dataset.citation.add_ds_description(value=metadata.get("description", ""))

        authors = metadata.get("author", [])
        for i, author in enumerate(authors):
            full_name = f"{author.get('familyName')}, {author.get('givenName')}" \
                if author.get("familyName") and author.get("givenName") \
                else author.get("name")
            affiliation_name = ""
            if affiliation_dict := author.get("affiliation"):
                affiliation_name = affiliation_dict.get("legalName", "")
            dataset.citation.add_author(name=full_name, affiliation=affiliation_name)
            if i == 0:
                dataset.citation.add_dataset_contact(name=full_name, email=author.get("email"))

        if date_published := metadata.get("datePublished"):
            dataset.citation.date_of_deposit = date_published
        # TODO look for "version" or something similar in dataverse
        # if version := metadata.get("version"):
        #     dataset.citation.softwareVersion = version
        if keywords := metadata.get("keywords", []):
            if keywords is list:
                for keyword in keywords:
                    dataset.citation.add_keyword(keyword)
        if deposition_license := metadata.get("license"):
            try:
                dataverse_license = License.fetch_by_name(deposition_license, server_url=self.client.server_url)
                dataset.citation.license = dataverse_license
            except Exception as e:
                _log.warning(f"Could not match license '{deposition_license}' to allowed licenses for deposition: {e}")
        dataset.citation.other_references = [f"Compiled by HERMES ({hermes_doi})"]

    def create_initial_version(self) -> None:
        """
        Creates an initial version of a publication.
        The original DepositPlugin flow with first creating the initial version and then adding metadata doesn't
        fit well with easyDataverse module since it requires certain metadata field to create the initial version.
        As solution, we use update_metadata_on_dataset(dataset) both in this method and in update_metadata().
        """
        if not self.command.args.initial:
            raise RuntimeError("Please use `--initial` to make an initial deposition.")
        dataset = self.client.create_dataset()
        self.update_metadata_on_dataset(dataset)
        persistent_id = dataset.upload(dataverse_name=self.config.target_collection)
        self.ctx.update(self.ctx_path["persistentId"], persistent_id)

    def create_new_version(self) -> None:
        """
        Creates a new version of an existing publication.
        TODO implement this
        """
        persistent_id = self.ctx[self.ctx_path["persistentId"]]
        if not persistent_id:
            raise RuntimeError("No persistent ID found in context. Cannot create new version.")
        dataset = self.client.load_dataset(persistent_id)
        if not dataset:
            raise RuntimeError(f"Could not load dataset for persistent ID {persistent_id}")
        _log.warning("Creating a new version of a dataset is not implemented right now.")

    def update_metadata(self) -> None:
        """
        Updates the dataset's metadata if the dataset is not newly created.
        If it is newly created, update_metadata_on_dataset was already called in create_initial_version.
        """
        if not self.command.args.initial:
            persistent_id = self.ctx[self.ctx_path["persistentId"]]
            dataset = self.client.load_dataset(persistent_id)
            self.update_metadata_on_dataset(dataset)
            res = dataset.update()
            if not res.ok:
                raise RuntimeError(f"Failed to update metadata: {res.status_code}: {res.text}")

    def upload_artifacts(self) -> None:
        """
        Uploads new artifacts to the current dataverse-dataset.
        """
        persistent_id = self.ctx[self.ctx_path["persistentId"]]
        dataset = self.client.load_dataset(persistent_id)
        files = *self.config.files, *[f[0] for f in self.command.args.file]
        for path_string in files:
            path_string = str(path_string)
            dataset.add_file(path_string)
        dataset.update()

    def publish(self) -> None:
        """
        Publishes the newly created dataset / publication.
        Unfortunately easyDataverse module does not support publishing. So we do that with requests.
        """
        persistent_id = self.ctx[self.ctx_path["persistentId"]]
        url = f"{self.config.site_url}/api/datasets/:persistentId/actions/:publish"
        params = {"type": "major"}
        headers = {"X-Dataverse-key": self.config.api_token}
        res = requests.post(url, headers=headers, params=params, data={"persistentId": persistent_id})
        if not res.ok:
            raise RuntimeError(f"Publish failed: {res.status_code}: {res.text}")
