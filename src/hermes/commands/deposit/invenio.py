# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

import json
import logging
from datetime import date, datetime

import click

from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath

from .error import DepositionUnauthorizedError


# TODO: It turns out that the schema downloaded here can not be used. Figure out what to
# do with this. Maybe the code can be removed.
def prepare_deposit(click_ctx: click.Context, ctx: CodeMetaContext):
    """Prepare the Invenio deposit.

    In this case, "prepare" means download the record schema that is required
    by Invenio instances. This is the basis that will be used for metadata
    mapping in the next step.
    """

    invenio_path = ContextPath.parse("deposit.invenio")

    invenio_ctx = ctx[invenio_path]
    # TODO: Get these values from config with reasonable defaults.
    recordSchemaUrl = f"{invenio_ctx['siteUrl']}/{invenio_ctx['schemaPaths']['record']}"

    # TODO: cache this download in HERMES cache dir
    # TODO: ensure to use from cache instead of download if not expired (needs config)
    response = click_ctx.session.get(recordSchemaUrl)
    response.raise_for_status()
    recordSchema = response.json()
    ctx.update(invenio_path["requiredSchema"], recordSchema)


def map_metadata(click_ctx: click.Context, ctx: CodeMetaContext):
    """Map the harvested metadata onto the Invenio schema."""

    deposition_metadata = _codemeta_to_invenio_deposition(ctx["codemeta"])

    metadata_path = ContextPath.parse("deposit.invenio.depositionMetadata")
    ctx.update(metadata_path, deposition_metadata)


def deposit(click_ctx: click.Context, ctx: CodeMetaContext):
    """Make a deposition on an Invenio-based platform.

    This function can:

    - Create a new record without any previous versions.

    Functionality to be added in the future:

    - Update the metadata of an existing record
    - Update the metadata and files of an existing record by creating a new version
    """

    _log = logging.getLogger("cli.deposit.invenio")

    invenio_path = ContextPath.parse("deposit.invenio")
    invenio_ctx = ctx[invenio_path]

    if not click_ctx.auth_token:
        raise DepositionUnauthorizedError("No auth token given for deposition platform")
    click_ctx.session.headers["Authorization"] = f"Bearer {click_ctx.auth_token}"

    # TODO: Get this from config or determine from some value (DOI, ...) in config.
    existing_record_url = None

    deposit_url = f"{invenio_ctx['siteUrl']}/{invenio_ctx['apiPaths']['depositions']}"
    if existing_record_url is not None:
        # TODO: Get by calling new version on existing record
        deposit_url = None
        raise NotImplementedError(
            "At the moment, hermes can not create new versions of existing records"
        )

    deposition_metadata = invenio_ctx["depositionMetadata"]
    response = click_ctx.session.post(
        deposit_url,
        json={"metadata": deposition_metadata}
    )
    response.raise_for_status()

    deposit = response.json()
    _log.debug("Created deposit: %s", deposit["links"]["html"])

    # ``deposit["metadata"]`` contains a ``prereserve_doi`` field which is a dict like
    # this: ``{'doi': '10.5072/zenodo.1234567', 'recid': 1234567}``. The ``recid`` can
    # be used to construct the URL to the record when published:
    # ``f"https://sandbox.zenodo.org/record/{recid}"``.
    # TODO: Use the URL and the DOI to update the data in the repo files before
    # uploading them.

    # TODO: When updating existing releases, the files API can be used to delete
    # existing files. GET ``deposit["links"]["files"]`` for a list of ``files`` (names,
    # checksums, ...), then DELETE ``file["links"]["download"]`` for each ``file`` in
    # the list.

    # Upload the files. We'll use the bucket API rather than the files API as it
    # supports file sizes above 100MB.
    bucket_url = deposit["links"]["bucket"]
    file_name, file_content = _get_file_for_upload(deposition_metadata)

    # TODO: When uploading real files, open them in binary mode and pass the handle to
    # the data kwarg. For now we'll upload just this one file.
    # TODO: Do we need to URL-encode the ``file_name`` or does this always work?
    response = click_ctx.session.put(
        f"{bucket_url}/{file_name}",
        data=file_content.encode()
    )
    response.raise_for_status()

    # This can potentially be used to verify the checksum
    # file_resource = response.json()

    publish_url = deposit["links"]["publish"]
    response = click_ctx.session.post(publish_url)
    response.raise_for_status()

    record = response.json()
    _log.info("Published record: %s", record["links"]["record_html"])


def _codemeta_to_invenio_deposition(metadata: dict) -> dict:
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
        for contributor in metadata["contributor"] if contributor.get("name") != "GitHub"
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
        # TODO: Get from config. This needs to be specified; we can not guess this.
        # TODO: Needs some more logic:
        # Possible options are: open, embargoed, restricted, closed. open and
        # restricted should come with a `license`, embargoed with an `embargo_date`,
        # restricted with `access_conditions`.
        "access_right": "open",
        # TODO: Get this from config/codemeta/GitHub API/...
        "license": "Apache-2.0",
        "embargo_date": None,
        "access_conditions": None,
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
        # TODO: This has to come from config.
        "communities": None,
        "grants": None,
        "subjects": None,
        # TODO: Get this from config
        "version": None,
    }.items() if v is not None}

    return deposition_metadata


def _get_file_for_upload(deposition_metadata: dict):
    """Return a file name and some content to test the file upload with."""

    timestamp = datetime.now().isoformat()
    metadata_json = json.dumps(deposition_metadata, indent=2)
    file_name = "README.md"
    file_content = f"""# {deposition_metadata["title"]}

{deposition_metadata["description"]}

Here's a timestamp so that the file changes and we can create a new version of the record later: `{timestamp}`

```json
{metadata_json}
```
"""

    return file_name, file_content
