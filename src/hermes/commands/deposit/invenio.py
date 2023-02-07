# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from datetime import date

import requests

from hermes.model.context import CodeMetaContext
from hermes.model.path import ContextPath


# TODO: It turns out that the schema downloaded here can not be used. Figure out what to
# do with this. Maybe the code can be removed.
def prepare_deposit(ctx: CodeMetaContext):
    """Prepare the Invenio deposit.

    In this case, "prepare" means download the record schema that is required
    by Invenio instances. This is the basis that will be used for metadata
    mapping in the next step.
    """

    invenio_path = ContextPath.parse("deposit.invenio")

    invenio_ctx = ctx[invenio_path]
    # TODO: Get these values from config with reasonable defaults.
    recordSchemaUrl = f"{invenio_ctx['siteUrl']}/{invenio_ctx['recordSchemaPath']}"

    # TODO: cache this download in HERMES cache dir
    # TODO: ensure to use from cache instead of download if not expired (needs config)
    recordSchema = _request_json(recordSchemaUrl)
    ctx.update(invenio_path["requiredSchema"], recordSchema)


def map_metadata(ctx: CodeMetaContext):
    """Map the harvested metadata onto the Invenio schema."""

    deposition_metadata = _codemeta_to_invenio_deposition(ctx["codemeta"])

    metadata_path = ContextPath.parse("deposit.invenio.depositionMetadata")
    ctx.update(metadata_path, deposition_metadata)

def deposit(ctx: CodeMetaContext):
    pass


def _request_json(url: str) -> dict:
    """Request an URL and return the JSON response as dict."""

    # TODO: Store a requests.Session in a click_ctx in case we need it more frequently?
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


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
