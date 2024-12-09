# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf (HZDR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: David Pape

from hermes.commands.deposit.invenio import (
    InvenioClient,
    InvenioDepositPlugin,
    InvenioDepositSettings,
    InvenioResolver,
)
from hermes.error import MisconfigurationError


class RodareDepositSettings(InvenioDepositSettings):
    """Settings for Rodare deposit plugin.

    This extends the base class by the Robis publication identifier that is required
    when creating deposits on Rodare.

    The ``site_url`` is overridden as it will be the same for all users.
    """

    site_url: str = "https://rodare.hzdr.de"
    robis_pub_id: str = None


class RodareClient(InvenioClient):
    """Custom Rodare client with updated ``platform_name`` for correct config access."""

    platform_name = "rodare"


class RodareResolver(InvenioResolver):
    """Custom Rodare resolver using custom client."""

    invenio_client_class = RodareClient


class RodareDepositPlugin(InvenioDepositPlugin):
    """Deposit plugin for the HZDR data repository Rodare (https://rodare.hzdr.de)."""

    platform_name = "rodare"
    settings_class = RodareDepositSettings
    invenio_client_class = RodareClient
    invenio_resolver_class = RodareResolver
    robis_url = "https://www.hzdr.de/robis"
    robis_publication_url = "https://www.hzdr.de/publications/Publ-{pub_id}"

    def prepare(self) -> None:
        """Update the context with the Robis identifier from the config."""
        super().prepare()

        if not self.config.robis_pub_id:
            raise MisconfigurationError(
                f"deposit.{self.platform_name}.robis_pub_id is not configured. "
                "You can get a robis_pub_id by publishing the software via Robis. "
                f"HERMES may be used for subsequent releases. {self.robis_url}"
            )

        self.ctx.update(
            self.invenio_context_path["robis_pub_id"], self.config.robis_pub_id
        )

    def create_initial_version(self) -> None:
        """Disallow creation of initial versions using HERMES.

        HZDR publications must all be registered in Robis (https://www.hzdr.de/robis).
        There is a workflow in place that guides users from Robis to Rodare and
        automatically transfers metadata for them. Starting the publication workflow in
        Rodare is discouraged.

        Subsequent releases of the software may be published on Rodare directly as the
        connection to Robis is in place by then.

        This code should never be reached. So, raising a ``RuntimeError`` is just a
        precaution.
        """
        raise RuntimeError(
            "Please initiate the publication process in Robis. "
            f"HERMES may be used for subsequent releases. {self.robis_url}"
        )

    def related_identifiers(self):
        """Update the related identifiers with link to Robis.

        Add the Robis Publ-Id as a related identifier. This is additional metadata which
        is not required by Rodare or Robis. It helps users find the related publication
        on Robis at ``https://www.hzdr.de/publications/Publ-{pub_id}``.

        An example publication on Rodare: https://rodare.hzdr.de/api/records/2

        The associated Robis page: https://www.hzdr.de/publications/Publ-27151
        """
        identifiers = super().related_identifiers()
        identifiers.append(
            {
                "identifier": self.robis_publication_url.format(
                    pub_id=self.config.robis_pub_id
                ),
                "relation": "isIdenticalTo",
                "scheme": "url",
            }
        )
        return identifiers

    def _codemeta_to_invenio_deposition(self) -> dict:
        """Update the deposition metadata with Robis Publ-Id.

        Deposits on Rodare require a connection to the publication database Robis. To
        make this connection, the deposit metadata has to contain the field ``pub_id``.
        """
        deposition_metadata = super()._codemeta_to_invenio_deposition()
        deposition_metadata["pub_id"] = self.config.robis_pub_id
        return deposition_metadata
