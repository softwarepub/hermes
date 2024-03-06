# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Oliver Bertuch
# SPDX-FileContributor: Michael Meinel

import typing as t

from requests import HTTPError

from hermes.commands.deposit.invenio import InvenioClient, InvenioDepositPlugin, InvenioResolver


class InvenioRDMClient(InvenioClient):
    DEFAULT_LICENSES_API_PATH = "api/vocabularies/licenses"
    platform_name = "invenio_rdm"

    def get_license(self, license_id: str):
        return super().get_license(license_id.casefold())

    def get_licenses(self):
        return self.get(f"{self.site_url}/{self.licenses_api_path}?size=1000")


class InvenioRDMResolver(InvenioResolver):
    invenio_client_class = InvenioRDMClient

    def resolve_license_id(self, license_url: t.Optional[str]) -> t.Optional[dict]:
        """Deliberately try to resolve the license URL to a valid InvenioRDM license information record from the
        vocabulary.

        First, this method tries to find the license URL in the list of known license vocabulary (which is fetched each
        time, ouch...).

        If the URL is not found (what is pretty probable by now, as CFFConvert produces SPDX-URLs while InvenioRDM still
        relies on the overhauled opensource.org URLs), the SPDX information record is fetched and all valid cross
        references are sought for.

        :return: The vocabulary record that is provided by InvenioRDM.
        """

        # First try to resolve using the simple way that worked well with Zenodo before InvenioRDM
        try:
            return super().resolve_license_id(license_url)
        except HTTPError:
            pass

        # If the easy "mapping" did not work, we really need to "search" for the correct license ID.
        response = self.client.get_licenses()
        response.raise_for_status()
        valid_licenses = response.json()

        license_info = self._search_license_info(license_url, valid_licenses)
        if license_info is None and license_url.startswith('https://spdx.org/licenses/'):
            response = self.client.get(f"{license_url}.json")
            response.raise_for_status()

            for license_cross_ref in response.json()['crossRef']:
                if not license_cross_ref['isValid']:
                    continue

                license_info = self._search_license_info(license_cross_ref["url"], valid_licenses)
                if license_info is not None:
                    break
            else:
                raise RuntimeError(f"Could not resolve license URL {license_url} to a valid identifier.")

        return license_info

    def _search_license_info(self, _url: str, valid_licenses: dict) -> t.Optional[dict]:
        for license_info in valid_licenses['hits']['hits']:
            try:
                if license_info['props']['url'] == _url:
                    return license_info
            except KeyError:
                continue
        else:
            return None


class IvenioRDMDepositPlugin(InvenioDepositPlugin):
    platform_name = "invenio_rdm"
    invenio_client_class = InvenioRDMClient
    invenio_resolver_class = InvenioRDMResolver
