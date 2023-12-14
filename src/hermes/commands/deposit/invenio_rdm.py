# SPDX-FileCopyrightText: 2023 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape
# SPDX-FileContributor: Oliver Bertuch
# SPDX-FileContributor: Michael Meinel

from hermes.commands.deposit.invenio import (
    InvenioClient,
    InvenioDepositPlugin,
    InvenioResolver,
)


class InvenioRDMClient(InvenioClient):
    DEFAULT_LICENSES_API_PATH = "api/vocabularies/licenses"
    platform_name = "invenio_rdm"

    def get_license(self, license_id: str):
        return super().get_license(license_id.casefold())

    def get_licenses(self):
        return self.get(f"{self.site_url}/{self.licenses_api_path}?size=1000")


class InvenioRDMResolver(InvenioResolver):
    invenio_client_class = InvenioRDMClient


class IvenioRDMDepositPlugin(InvenioDepositPlugin):

    platform_name = "invenio_rdm"
    invenio_client_class = InvenioRDMClient
    invenio_resolver_class = InvenioRDMResolver

    def _get_license_identifier(self):
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

        An API endpoint (usually ``/api/vocabularies/licenses``) can be used to check whether a given
        license is supported by the Invenio instance. This function tries to retrieve the
        license by lower-casing the identifier at the end of the license URL path. If this identifier
        does not exist on the Invenio instance, all available licenses are fetched and the URL is sought
        for in the results. However, this might again not lead to success (as Invenio still provides
        the obsolete https://opensource.org URLs) but harvesters might provide the SPDX style URLs.
        Hence, the license URL is checked whether it is pointing to https://spdx.org/licenses/ and if
        this is the case, the license record from SPDX is fetched and all `crossRef` URLs that are flagged
        `isValid` are again sought for in the full set of licenses. Only if this still fails,
        a :class:`RuntimeError` is raised.

        If no license is given in the CodeMeta, ``None`` is returned.
        """

        try:
            return super()._get_license_identifier()
        except RuntimeError:
            pass

        # Second try: Fetch full list of licenses available... maybe we should cache this.
        license_info = self._look_up_license_info()
        return license_info["id"]

    def _look_up_license_info(self):
        """Deliberately try to resolve the license URL to a valid InvenioRDM license information record from the
        vocabulary.

        First, this method tries to find the license URL in the list of known license vocabulary (which is fetched each
        time, ouch...).

        If the URL is not found (what is pretty probable by now, as CFFConvert produces SPDX-URLs while InvenioRDM still
        relies on the overhauled opensource.org URLs), the SPDX information record is fetched and all valid cross
        references are sought for.

        :return: The vocabulary record that is provided by InvenioRDM.
        """
        response = self.client.get_licenses()
        response.raise_for_status()
        valid_licenses = response.json()

        def _search_license_info(_url):
            for license_info in valid_licenses['hits']['hits']:
                try:
                    if license_info['props']['url'] == _url:
                        return license_info
                except KeyError:
                    continue
            else:
                return None

        license_url = self.ctx["codemeta"].get("license")
        license_info = _search_license_info(license_url)
        if license_info is None and license_url.startswith('https://spdx.org/licenses/'):
            response = self.client.get(f"{license_url}.json")
            response.raise_for_status()

            for license_cross_ref in response.json()['crossRef']:
                if not license_cross_ref['isValid']:
                    continue

                license_info = _search_license_info(license_cross_ref["url"])
                if license_info is not None:
                    break
            else:
                raise RuntimeError(f"Could not resolve license URL {license_url} to a valid identifier.")

        return license_info
