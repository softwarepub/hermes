# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape

from unittest import mock

import pytest

from hermes.commands.deposit import invenio
from hermes.error import MisconfigurationError


def test_resolve_doi(requests_mock):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://foo.bar/record/6789'})
    requests_mock.get('https://foo.bar/record/6789')

    assert invenio._invenio_resolve_doi('https://foo.bar', '123.45/foo.bar-6789') == '6789'


def test_resolve_doi_wrong_host(requests_mock):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://foo.baz/record/6789'})
    requests_mock.get('https://foo.baz/record/6789')

    with pytest.raises(ValueError):
        invenio._invenio_resolve_doi('https://foo.bar', '123.45/foo.bar-6789')


def test_resolve_doi_unknown(requests_mock):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://datacite.org/404.html'})

    # To show how broken datacite is right now
    requests_mock.get('https://datacite.org/404.html', status_code=200)

    with pytest.raises(ValueError):
        invenio._invenio_resolve_doi('https://foo.bar', '123.45/foo.bar-6789')


def test_resolve_record_id(requests_mock):
    requests_mock.get('https://foo.bar/api/records/6789',
                      text='{"links":{"latest":"https://foo.bar/api/records/12345"}}')
    requests_mock.get('https://foo.bar/api/records/12345', text='{"id":"12345","metadata":{"mock":42}}')

    assert invenio._invenio_resolve_record_id('https://foo.bar', '6789') == ('12345', {"mock": 42})


def test_resolve_record_id_unknown(requests_mock):
    requests_mock.get('https://foo.bar/api/records/6789', status_code=404, text="Not found")

    with pytest.raises(ValueError):
        invenio._invenio_resolve_record_id('https://foo.bar', '6789')


def test_resolve_record_id_latest_unknown(requests_mock):
    requests_mock.get('https://foo.bar/api/records/6789',
                      text='{"links":{"latest":"https://foo.bar/api/records/12345"}}')
    requests_mock.get('https://foo.bar/api/records/12345', status_code=404)

    with pytest.raises(ValueError):
        invenio._invenio_resolve_record_id('https://foo.bar', '6789')


def test_get_access_modalities_closed():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'closed',
            }
        }
        access_right, _, _ = invenio._get_access_modalities(None)
        assert access_right == "closed"


def test_get_access_modalities_embargoed_no_date_no_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'embargoed',
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities(None)


def test_get_access_modalities_embargoed_no_date_with_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'embargoed',
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities("Apache-2.0")


def test_get_access_modalities_embargoed_with_date_with_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'embargoed',
                'embargo_date': '2050-05-01',
            }
        }
        access_right, embargo_date, _ = invenio._get_access_modalities("Apache-2.0")
        assert access_right == "embargoed"
        assert embargo_date == "2050-05-01"


def test_get_access_modalities_embargoed_with_broken_date_with_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'embargoed',
                'embargo_date': 'not-a-date',
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities("Apache-2.0")


def test_get_access_modalities_restricted_no_conditions():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'restricted',
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities(None)


def test_get_access_modalities_restricted_with_conditions():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'restricted',
                'access_conditions': 'You must be cool',
            }
        }
        access_right, _, access_conditions = invenio._get_access_modalities(None)
        assert access_right == "restricted"
        assert access_conditions == "You must be cool"


def test_get_access_modalities_open_no_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'open',
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities(None)


def test_get_access_modalities_open_with_license():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'open',
            }
        }
        access_right, _, _ = invenio._get_access_modalities("Apache-2.0")
        assert access_right == "open"


def test_get_access_modalities_broken_access_right():
    with mock.patch("hermes.config.get") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            'invenio': {
                'access_right': 'unknown',  # does not exist
            }
        }
        with pytest.raises(MisconfigurationError):
            invenio._get_access_modalities(None)
