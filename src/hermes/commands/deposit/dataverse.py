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
        super().__init__(command, ctx)
        self.config = getattr(self.command.settings, self.platform_name)
        api_token = self.config.api_token
        if not api_token:
            raise DepositionUnauthorizedError("No valid auth token given for deposition platform")
        self.client = Dataverse(server_url=self.config.site_url, api_token=api_token)
        self.ctx_path = ContextPath.parse(f"deposit.{self.platform_name}")

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

    def update_metadata_on_dataset(self, dataset: Dataset):
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
