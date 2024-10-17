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
    site_url: str = "https://rodare.hzdr.de"
    robis_pub_id: str = None


class RodareClient(InvenioClient):
    platform_name = "rodare"


class RodareResolver(InvenioResolver):
    invenio_client_class = RodareClient


class RodareDepositPlugin(InvenioDepositPlugin):
    platform_name = "rodare"
    settings_class = RodareDepositSettings
    invenio_client_class = RodareClient
    invenio_resolver_class = RodareResolver
    robis_url = "https://www.hzdr.de/robis"

    def prepare(self) -> None:
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
        raise RuntimeError(
            "Please initiate the publication process in Robis. "
            f"HERMES may be used for subsequent releases. {self.robis_url}"
        )

    def _codemeta_to_invenio_deposition(self) -> dict:
        pub_id = self.config.robis_pub_id
        deposition_metadata = super()._codemeta_to_invenio_deposition()

        robis_identifier = {
            "identifier": f"https://www.hzdr.de/publications/Publ-{pub_id}",
            "relation": "isIdenticalTo",
            "scheme": "url",
        }

        related_identifiers: list = deposition_metadata.get("related_identifiers", [])
        related_identifiers.append(robis_identifier)

        deposition_metadata["related_identifiers"] = related_identifiers
        deposition_metadata["pub_id"] = pub_id

        return deposition_metadata
