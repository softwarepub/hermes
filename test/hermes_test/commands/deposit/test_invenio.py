# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import pytest

from hermes.commands.deposit import invenio


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
    requests_mock.get('https://foo.bar/api/records/12345', text='{"id":"12345"}')

    assert invenio._invenio_resolve_record_id('https://foo.bar', '6789') == '12345'


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
