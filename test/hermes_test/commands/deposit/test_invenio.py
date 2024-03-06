# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: David Pape

from unittest import mock

import click
import pytest

from hermes.commands.deposit import invenio
from hermes.error import MisconfigurationError


@pytest.fixture
def resolver():
    with mock.patch("hermes.logger.config.deposit") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            "invenio": {
                "site_url": "https://invenio.example.com",
            }
        }
        r = invenio.InvenioResolver()
    return r


@pytest.fixture
def depositor():
    click_ctx = click.Context(click.Command("deposit"))
    click_ctx.params.update({"auth_token": ""})
    with mock.patch("hermes.logger.config.deposit") as mocked_deposit_config:
        mocked_deposit_config.return_value = {
            "invenio": {
                "site_url": "https://invenio.example.com",
            }
        }
        d = invenio.InvenioDepositPlugin(click_ctx, None)
    return d


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_doi(requests_mock, resolver):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://invenio.example.com/record/6789'})
    requests_mock.get('https://invenio.example.com/record/6789')

    assert resolver.resolve_doi('123.45/foo.bar-6789') == '6789'


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_doi_wrong_host(requests_mock, resolver):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://not.invenio.example.com/record/6789'})
    requests_mock.get('https://not.invenio.example.com/record/6789')

    with pytest.raises(ValueError):
        resolver.resolve_doi('123.45/foo.bar-6789')


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_doi_unknown(requests_mock, resolver):
    requests_mock.get('https://doi.org/123.45/foo.bar-6789',
                      status_code=302,
                      headers={'Location': 'https://datacite.org/404.html'})

    # To show how broken datacite is right now
    requests_mock.get('https://datacite.org/404.html', status_code=200)

    with pytest.raises(ValueError):
        resolver.resolve_doi('123.45/foo.bar-6789')


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_record_id(requests_mock, resolver):
    requests_mock.get('https://invenio.example.com/api/records/6789',
                      text='{"links":{"latest":"https://invenio.example.com/api/records/12345"}}')
    requests_mock.get('https://invenio.example.com/api/records/12345', text='{"id":"12345","metadata":{"mock":42}}')

    assert resolver.resolve_record_id('6789') == ('12345', {"mock": 42})


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_record_id_unknown(requests_mock, resolver):
    requests_mock.get('https://invenio.example.com/api/records/6789', status_code=404, text="Not found")

    with pytest.raises(ValueError):
        resolver.resolve_record_id('6789')


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_resolve_record_id_latest_unknown(requests_mock, resolver):
    requests_mock.get('https://invenio.example.com/api/records/6789',
                      text='{"links":{"latest":"https://invenio.example.com/api/records/12345"}}')
    requests_mock.get('https://invenio.example.com/api/records/12345', status_code=404)

    with pytest.raises(ValueError):
        resolver.resolve_record_id('6789')


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_closed(depositor):
    depositor.config.update({'access_right': 'closed'})
    access_right, _, _ = depositor._get_access_modalities(None)
    assert access_right == "closed"


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_embargoed_no_date_no_license(depositor):
    depositor.config.update({'access_right': 'embargoed'})
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities(None)


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_embargoed_no_date_with_license(depositor):
    depositor.config.update({'access_right': 'embargoed'})
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities("Apache-2.0")


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_embargoed_with_date_with_license(depositor):
    depositor.config.update({
        'access_right': 'embargoed',
        'embargo_date': '2050-05-01',
    })
    access_right, embargo_date, _ = depositor._get_access_modalities("Apache-2.0")
    assert access_right == "embargoed"
    assert embargo_date == "2050-05-01"


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_embargoed_with_broken_date_with_license(depositor):
    depositor.config.update({
        'access_right': 'embargoed',
        'embargo_date': 'not-a-date',
    })
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities("Apache-2.0")


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_restricted_no_conditions(depositor):
    depositor.config.update({'access_right': 'restricted'})
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities(None)


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_restricted_with_conditions(depositor):
    depositor.config.update({
        'access_right': 'restricted',
        'access_conditions': 'You must be cool',
    })
    access_right, _, access_conditions = depositor._get_access_modalities(None)
    assert access_right == "restricted"
    assert access_conditions == "You must be cool"


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_open_no_license(depositor):
    depositor.config.update({'access_right': 'open'})
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities(None)


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_open_with_license(depositor):
    depositor.config.update({'access_right': 'open'})
    access_right, _, _ = depositor._get_access_modalities("Apache-2.0")
    assert access_right == "open"


@pytest.mark.skip(reason="pydantic-settings need to be refactored")
def test_get_access_modalities_broken_access_right(depositor):
    depositor.config.update({
        'access_right': 'unknown',  # does not exist
    })
    with pytest.raises(MisconfigurationError):
        depositor._get_access_modalities(None)
