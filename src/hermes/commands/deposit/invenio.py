# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Oliver Bertuch
# SPDX-FileContributor: Michael Meinel

import json
import logging
import pathlib
import typing as t
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from pydantic import BaseModel

from hermes.commands.deposit.base import BaseDepositPlugin, HermesDepositCommand
from hermes.commands.deposit.error import DepositionUnauthorizedError
from hermes.error import MisconfigurationError
from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath
from hermes.utils import hermes_user_agent


_log = logging.getLogger("cli.deposit.invenio")


class InvenioClient(requests.Session):
    DEFAULT_LICENSES_API_PATH = "api/licenses"
    DEFAULT_COMMUNITIES_API_PATH = "api/communities"
    DEFAULT_DEPOSITIONS_API_PATH = "api/deposit/depositions"
    DEFAULT_RECORDS_API_PATH = "api/records"

    # Used for context path and config
    platform_name = "invenio"

    def __init__(self, config, auth_token=None, platform_name=None) -> None:
        super().__init__()

        if platform_name is not None:
            self.platform_name = platform_name

        self.config = config
        self.headers.update({"User-Agent": hermes_user_agent})

        self.auth_token = auth_token
        self.site_url = self.config.site_url
        if not self.site_url:
            raise MisconfigurationError(f"deposit.{self.platform_name}.site_url is not configured")

    def request(self, method, url, headers=None, **kwargs) -> requests.Response:
        """Overridden request method to automatically set Authorization header for all requests to the configured site.

        See [requests documentation](https://requests.readthedocs.io/en/latest/api.html#requests.request) for details.
        """

        if self.auth_token:
            if urlparse(self.site_url).hostname == urlparse(url).hostname:
                headers = (headers or {}) | {"Authorization": f"Bearer {self.auth_token}"}
        return super().request(method, url, headers=headers, **kwargs)

    def get_record(self, record_id):
        return self.get(f"{self.site_url}/{self.records_api_path}/{record_id}")

    def get_deposit(self, latest_record_id):
        return self.get(
            f"{self.site_url}/{self.depositions_api_path}/{latest_record_id}"
        )

    def get_license(self, license_id):
        return self.get(f"{self.site_url}/{self.licenses_api_path}/{license_id}")

    def get_community(self, community_id):
        return self.get(f"{self.site_url}/{self.communities_api_path}/{community_id}")

    def new_deposit(self):
        return self.post(f"{self.site_url}/{self.depositions_api_path}", json={})

    @property
    def api_paths(self):
        return self.config.api_paths

    @property
    def licenses_api_path(self):
        return self.api_paths.get("licenses", self.DEFAULT_LICENSES_API_PATH)

    @property
    def communities_api_path(self):
        return self.api_paths.get("communities", self.DEFAULT_COMMUNITIES_API_PATH)

    @property
    def depositions_api_path(self):
        return self.api_paths.get("depositions", self.DEFAULT_DEPOSITIONS_API_PATH)

    @property
    def records_api_path(self):
        return self.api_paths.get("records", self.DEFAULT_RECORDS_API_PATH)


class InvenioResolver:

    invenio_client_class = InvenioClient

    def __init__(self, client=None):
        self.client = client or self.invenio_client_class()

    def resolve_latest_id(
        self, record_id=None, doi=None, codemeta_identifier=None
    ) -> t.Tuple[t.Optional[str], dict]:
        """
        Using the given metadata parameters, figure out the latest record id.

        If ``record_id`` is given, it will be used to identify the latest version of the
        record. Otherwise, if there is a DOI present (either as ``doi`` parameter or as
        ``codemeta_identifier``), the DOI will be used to resolve the base record id.

        Either way the record id will be used to resolve the latest version.

        If any of the resolution steps fail or produce an unexpected result, a
        ``ValueError`` will be raised.
        """

        # Check if we configured an Invenio record ID (of the concept...)

        if record_id is None:
            if doi is None:
                if codemeta_identifier is not None:
                    # TODO: There might be more semantic in the codemeta.identifier... (also see schema.org)
                    if codemeta_identifier.startswith('https://doi.org/'):
                        doi = codemeta_identifier[16:]
                    elif codemeta_identifier.startswith('http://dx.doi.org/'):
                        doi = codemeta_identifier[18:]

            if doi is not None:
                # If we got a DOI, resolve it (using doi.org) into a Invenio URL ... and extract the record id.
                record_id = self.resolve_doi(doi)

        if record_id is not None:
            # If we got a record id by now, resolve it using the Invenio API to the latests record.
            return self.resolve_record_id(record_id)

        return None, {}

    def resolve_doi(self, doi) -> str:
        """
        Resolve a DOI to an Invenio URL and extract the record id.

        :param doi: The DOI to be resolved (only the identifier *without* the ``https://doi.org/`` prefix).
        :return: The record ID on the respective instance.
        """

        res = self.client.get(f'https://doi.org/{doi}')

        # This is a mean hack due to DataCite answering a 404 with a 200 status
        if res.url == 'https://datacite.org/404.html':
            raise ValueError(f"Invalid DOI: {doi}")

        # Ensure the resolved record is on the correct instance
        if not res.url.startswith(self.client.site_url):
            raise ValueError(f"{res.url} is not on configured host {self.client.site_url}.")

        # Extract the record id as last part of the URL path
        page_url = urlparse(res.url)
        *_, record_id = page_url.path.split('/')
        return record_id

    def resolve_record_id(self, record_id: str) -> t.Tuple[str, dict]:
        """
        Find the latest version of a given record.

        :param record_id: The record that sould be resolved.
        :return: The record id of the latest version for the requested record.
        """
        res = self.client.get_record(record_id)
        if res.status_code != 200:
            raise ValueError(f"Could not retrieve record from {res.url}: {res.text}")

        res_json = res.json()
        res = self.client.get(res_json['links']['latest'])
        if res.status_code != 200:
            raise ValueError(f"Could not retrieve record from {res.url}: {res.text}")

        res_json = res.json()
        return res_json['id'], res_json['metadata']

    def resolve_license_id(self, license_url: t.Optional[str]) -> t.Optional[str]:
        """Get Invenio license representation from CodeMeta.

        The license to use is extracted from the ``license`` field in the
        :class:`CodeMetaContext` and converted into an appropiate license identifier to be
        passed to an Invenio instance.

        A license according to CodeMeta may be a URL (text) or a CreativeWork. This function
        only handles URLs. If a ``license`` field is present in the CodeMeta and it is not
        of type :class:`str`, a :class:`RuntimeError` is raised.

        Invenio instances take a license string which refers to a license identifier.
        Typically, Invenio instances offer licenses from https://opendefinition.org and
        https://spdx.org. However, it is possible to mint PIDs for custom licenses.

        An API endpoint (usually ``/api/licenses``) can be used to check whether a given
        license is supported by the Invenio instance. This function tries to retrieve the
        license by the identifier at the end of the license URL path. If this identifier
        does not exist on the Invenio instance, a :class:`RuntimeError` is raised. If no
        license is given in the CodeMeta, ``None`` is returned.
        """

        if license_url is None:
            return None

        if not isinstance(license_url, str):
            raise RuntimeError(
                "The given license in CodeMeta must be of type str. "
                "Licenses of type 'CreativeWork' are not supported."
            )

        parsed_url = urlparse(license_url)
        url_path = parsed_url.path.rstrip("/")
        license_id = url_path.split("/")[-1]

        response = self.client.get_license(license_id)
        if response.status_code == 404:
            raise RuntimeError(f"Not a valid license identifier: {license_id}")
        # Catch other problems
        response.raise_for_status()

        return response.json()["id"]


class InvenioDepositSettings(BaseModel):
    """Settings required to deposit into Invenio(RDM)."""

    site_url: str = ""

    communities: list[str] = None
    access_right: str = None
    embargo_date: str = None
    access_conditions: str = None
    api_paths: t.Dict = {}
    auth_token: str = ''
    files: list[pathlib.Path] = []

    record_id: int = None
    doi: str = None


class InvenioDepositPlugin(BaseDepositPlugin):

    platform_name = "invenio"
    invenio_client_class = InvenioClient
    invenio_resolver_class = InvenioResolver
    settings_class = InvenioDepositSettings

    def __init__(self, command: HermesDepositCommand, ctx: CodeMetaContext, client=None, resolver=None) -> None:
        super().__init__(command, ctx)

        self.invenio_context_path = ContextPath.parse(f"deposit.{self.platform_name}")
        self.invenio_ctx = None
        self.config = getattr(self.command.settings, self.platform_name)

        if client is None:
            auth_token = self.config.auth_token
            if not auth_token:
                raise DepositionUnauthorizedError("No valid auth token given for deposition platform")
            self.client = self.invenio_client_class(self.config,
                                                    auth_token=auth_token, platform_name=self.platform_name)
        else:
            self.client = client

        self.resolver = resolver or self.invenio_resolver_class(self.client)
        self.links = {}

    # TODO: Populate some data structure here? Or move more of this into __init__?
    def prepare(self) -> None:
        """Prepare the deposition on an Invenio-based platform.

        In this function we do the following:

        - resolve the latest published version of this publication (if any)
        - check whether the current version (given in the CodeMeta) was already published
        - check whether we have a valid license identifier (if any)
        - check wether the communities are valid (if configured)
        - check access modalities (access right, access conditions, embargo data, existence
          of license)
        - check whether required configuration options are present
        - update ``self.ctx`` with metadata collected during the checks
        """

        rec_id = self.config.record_id
        doi = self.config.doi

        try:
            codemeta_identifier = self.ctx["codemeta.identifier"]
        except KeyError:
            codemeta_identifier = None

        rec_id, rec_meta = self.resolver.resolve_latest_id(
            record_id=rec_id, doi=doi, codemeta_identifier=codemeta_identifier
        )

        version = self.ctx["codemeta"].get("version")
        if rec_meta and (version == rec_meta.get("version")):
            raise ValueError(f"Version {version} already deposited.")

        self.ctx.update(self.invenio_context_path['latestRecord'], {'id': rec_id, 'metadata': rec_meta})

        license = self._get_license_identifier()
        self.ctx.update(self.invenio_context_path["license"], license)

        communities = self._get_community_identifiers()
        self.ctx.update(self.invenio_context_path["communities"], communities)

        access_right, embargo_date, access_conditions = self._get_access_modalities(license)
        self.ctx.update(self.invenio_context_path["access_right"], access_right)
        self.ctx.update(self.invenio_context_path["embargo_date"], embargo_date)
        self.ctx.update(self.invenio_context_path["access_conditions"], access_conditions)

        self.invenio_ctx = self.ctx[self.invenio_context_path]

    def map_metadata(self) -> None:
        """Map the harvested metadata onto the Invenio schema."""

        deposition_metadata = self._codemeta_to_invenio_deposition()
        self.ctx.update(self.invenio_context_path["depositionMetadata"], deposition_metadata)

        # Store a snapshot of the mapped data within the cache, useful for analysis, debugging, etc
        with open(self.ctx.get_cache("deposit", self.platform_name, create=True), 'w') as invenio_json:
            json.dump(deposition_metadata, invenio_json, indent='  ')

    def is_initial_publication(self) -> bool:
        latest_record_id = self.invenio_ctx.get("latestRecord", {}).get("id")
        return latest_record_id is None

    def create_initial_version(self) -> None:
        """Create an initial version of a publication."""

        if not self.command.args.initial:
            raise RuntimeError("Please use `--initial` to make an initial deposition.")

        response = self.client.new_deposit()
        if not response.ok:
            _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
            raise RuntimeError(f"Could not create initial deposit {response.url!r}")

        deposit = response.json()
        self.links.update(deposit["links"])
        _log.debug("Created initial version deposit: %s", self.links["html"])

    def create_new_version(self) -> None:
        """Create a new version of an existing publication."""

        latest_record_id = self.invenio_ctx.get("latestRecord", {}).get("id")

        # Get current deposit
        response = self.client.get_deposit(latest_record_id)
        if not response.ok:
            _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
            raise RuntimeError(f"Failed to get current deposit {response.url!r}")

        self.links.update(response.json()["links"])

        # Create a new version using the newversion action
        deposit_url = self.links["newversion"]
        response = self.client.post(deposit_url)
        if not response.ok:
            _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
            raise RuntimeError(f"Could not create new version deposit {deposit_url!r}")

        # Store link to latest draft to be used in :func:`update_metadata`.
        old_deposit = response.json()
        self.links.update(old_deposit["links"])

    def update_metadata(self) -> None:
        """Update the metadata of a draft."""

        draft_url = self.links["latest_draft"]

        deposition_metadata = self.invenio_ctx["depositionMetadata"]

        response = self.client.put(
            draft_url,
            json={"metadata": deposition_metadata}
        )

        if not response.ok:
            _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
            raise RuntimeError(f"Could not update metadata of draft {draft_url!r}")

        deposit = response.json()
        self.links.update(deposit["links"])

        _log.debug("Created new version deposit: %s", self.links["html"])
        with open(self.ctx.get_cache('deposit', 'deposit', create=True), 'w') as deposit_file:
            json.dump(deposit, deposit_file, indent=4)

    def delete_artifacts(self) -> None:
        """Delete existing file artifacts.

        This is done so that files which existed in an earlier publication but don't exist
        any more, are removed. Otherwise they would cause an error because the didn't change
        between versions.
        """
        # TODO: This needs to be implemented!
        pass

    def upload_artifacts(self) -> None:
        """Upload file artifacts to the deposit.

        We'll use the bucket API rather than the files API as it supports file sizes above
        100MB.
        """

        bucket_url = self.links["bucket"]

        files = *self.config.files, *[f[0] for f in self.command.args.file]
        for path_arg in files:
            path = Path(path_arg)

            # This should not happen, as Click shall not accept dirs as arguments already. Zero trust anyway.
            if not path.is_file():
                raise ValueError(f"{path}: Any given argument to be included in the deposit must be a file.")

            with open(path, "rb") as file_content:
                response = self.client.put(
                    f"{bucket_url}/{path.name}", data=file_content,
                )
                if not response.ok:
                    _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
                    raise RuntimeError(f"Could not upload file {path.name!r} into bucket {bucket_url!r}")

            # This can potentially be used to verify the checksum
            # file_resource = response.json()

    def publish(self) -> None:
        """Publish the deposited record."""

        publish_url = self.links["publish"]
        response = self.client.post(publish_url)
        if not response.ok:
            _log.error("Server answered with error code %d:\n%s", response.status_code, response.text)
            raise RuntimeError(f"Could not publish deposit via {publish_url!r}")

        record = response.json()
        self.links.update(record["links"])

        _log.info("Published record: %s", self.links["record_html"])

    def _codemeta_to_invenio_deposition(self) -> dict:
        """The mapping logic.

        Functionality similar to this exists in the ``convert_codemeta`` package which uses
        the crosswalk tables to do the mapping:

        .. code-block:: python

          invenio_metadata = convert_codemeta.crosswalk(
              metadata, "codemeta", "Zenodo"
          )

        Unfortunately, this doesn't work well with additional metadata in the same dict, so
        it is safer to provide our own implementation.

        Currently, this function handles a lot of cases which we want to be able to
        configure. A simple mapping from one JSON path to another is not enough.

        The metadata expected by Zenodo is described in the `Zenodo Developers guide
        <https://developers.zenodo.org/#representation>`_. Unfortunately, there doesn't seem
        to be a schema one can download in order to validate these metadata. There might be
        differences between Invenio-based platforms.
        """

        metadata = self.ctx["codemeta"]
        license = self.invenio_ctx["license"]
        communities = self.invenio_ctx["communities"]
        access_right = self.invenio_ctx["access_right"]
        embargo_date = self.invenio_ctx["embargo_date"]
        access_conditions = self.invenio_ctx["access_conditions"]

        creators = [
            # TODO: Distinguish between @type "Person" and others
            {
                k: v for k, v in {
                    # TODO: This is ugly
                    "affiliation": author.get("affiliation", {"legalName": None}).get("legalName"),
                    # Invenio wants "family, given". author.get("name") might not have this format.
                    "name": f"{author.get('familyName')}, {author.get('givenName')}"
                    if author.get("familyName") and author.get("givenName")
                    else author.get("name"),
                    # Invenio expects the ORCID without the URL part
                    "orcid": author.get("@id", "").replace("https://orcid.org/", "") or None,
                }.items() if v is not None
            }
            for author in metadata["author"]
        ]

        # This is not used at the moment. See comment below in `deposition_metadata` dict.
        contributors = [  # noqa: F841
            # TODO: Distinguish between @type "Person" and others
            {
                k: v for k, v in {
                    # TODO: This is ugly
                    "affiliation": contributor.get("affiliation", {"legalName": None}).get("legalName"),
                    # Invenio wants "family, given". contributor.get("name") might not have this format.
                    "name": f"{contributor.get('familyName')}, {contributor.get('givenName')}"
                    if contributor.get("familyName") and contributor.get("givenName")
                    else contributor.get("name"),
                    # Invenio expects the ORCID without the URL part
                    "orcid": contributor.get("@id", "").replace("https://orcid.org/", "") or None,
                    # TODO: Many possibilities here. Get from config
                    "type": "ProjectMember",
                }.items() if v is not None
            }
            # TODO: Filtering out "GitHub" should be done elsewhere
            for contributor in metadata.get("contributor", []) if contributor.get("name") != "GitHub"
        ]

        # TODO: Use the fields currently set to `None`.
        # Some more fields are available but they most likely don't relate to software
        # publications targeted by hermes.
        deposition_metadata = {k: v for k, v in {
            # If upload_type is "publication"/"image", a publication_type/image_type must be
            # specified. Since hermes targets software publications, this can be ignored and
            # upload_type can be hard-coded to "software".
            # TODO: Make this a constant maybe.
            "upload_type": "software",
            # IS0 8601-formatted date
            # TODO: Maybe we want a different date? Then make this configurable. If not,
            # this can be removed as it defaults to today.
            "publication_date": date.today().isoformat(),
            "title": metadata["name"],
            "creators": creators,
            # TODO: Use a real description here. Possible sources could be
            # `tool.poetry.description` from pyproject.toml or `abstract` from
            # CITATION.cff. This should then be stored in codemeta description field.
            "description": metadata["name"],
            "access_right": access_right,
            "license": license,
            "embargo_date": embargo_date,
            "access_conditions": access_conditions,
            # TODO: If a publisher already has assigned a DOI to the files we want to
            # upload, it should be used here. In this case, Invenio will not give us a new
            # one. Set "prereserve_doi" accordingly.
            "doi": None,
            # This prereserves a DOI that can then be added to the files before publishing
            # them.
            # TODO: Use the DOI we get back from this.
            "prereserve_doi": True,
            # TODO: A good source for this could be `tool.poetry.keywords` in pyproject.toml.
            "keywords": None,
            "notes": None,
            "related_identifiers": None,
            # TODO: Use `contributors`. In the case of the hermes workflow itself, the
            # contributors are currently all in `creators` already. So for now, we set this
            # to `None`. Change this when relationship between authors and contributors can
            # be specified in the processing step.
            "contributors": None,
            "references": None,
            "communities": communities,
            "grants": None,
            "subjects": None,
            "version": metadata.get('version'),
        }.items() if v is not None}

        return deposition_metadata

    def _get_license_identifier(self) -> t.Optional[str]:
        """Get Invenio license identifier that matches the given license URL.

        If no license is configured, ``None``  will be returned.
        """
        license_url = self.ctx["codemeta"].get("license")
        return self.resolver.resolve_license_id(license_url)

    def _get_community_identifiers(self):
        """Get Invenio community identifiers from config.

        This function gets the communities to be used for the deposition on an Invenio-based
        site from the config and checks their validity against the site's API. If one of the
        identifiers can not be found on the site, a :class:`MisconfigurationError` is
        raised.
        """

        communities = self.config.communities
        if communities is None:
            return None

        community_ids = []
        for community_id in communities:
            response = self.client.get_community(community_id)
            if response.status_code == 404:
                raise MisconfigurationError(
                    f"Not a valid community identifier: {community_id}"
                )
            # Catch other problems
            response.raise_for_status()
            community_ids.append({"identifier": response.json()["id"]})

        return community_ids

    def _get_access_modalities(self, license):
        """Get access right, embargo date and access conditions based on configuration and given license.

        This function implements the rules laid out in the `Zenodo developer documentation
        <https://developers.zenodo.org/#representation>`_:

        - ``access_right`` is a controlled vocabulary
        - embargoed access depositions need an embargo date
        - restricted access depositions need access conditions
        - open and embargoed access depositions need a license
        - closed access depositions have no further requirements

        This function also makes sure that the given embargo date can be parsed as an ISO
        8601 string representation and that the access rights are given as a string.
        """
        access_right = self.config.access_right
        if access_right is None:
            raise MisconfigurationError(f"deposit.{self.platform_name}.access_right is not configured")

        access_right_options = ["open", "embargoed", "restricted", "closed"]
        if access_right not in access_right_options:
            raise MisconfigurationError(
                f"deposition.{self.platform_name}.access_right must be one of: "
                f"{', '.join(access_right_options)}"
            )

        embargo_date = self.config.embargo_date
        if access_right == "embargoed" and embargo_date is None:
            raise MisconfigurationError(
                f"With access_right {access_right}, "
                f"deposit.{self.platform_name}.embargo_date must be configured"
            )

        if embargo_date is not None:
            try:
                datetime.fromisoformat(embargo_date)
            except ValueError:
                raise MisconfigurationError(
                    f"Could not parse deposit.{self.platform_name}.embargo_date {embargo_date!r}. "
                    "Must be in ISO 8601 format."
                )

        access_conditions = self.config.access_conditions
        if access_right == "restricted" and access_conditions is None:
            raise MisconfigurationError(
                f"With access_right {access_right}, "
                f"deposit.{self.platform_name}.access_conditions must be configured"
            )

        if access_conditions is not None and not isinstance(access_conditions, str):
            raise MisconfigurationError(
                f"deposit.{self.platform_name}.access_conditions must be a string (HTML is allowed)."
            )

        if license is None and access_right in ["open", "embargoed"]:
            raise MisconfigurationError(
                f"With access_right {access_right}, a license is required."
            )

        if access_right == "closed":
            pass

        return access_right, embargo_date, access_conditions
