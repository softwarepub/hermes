# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche
# SPDX-FileContributor: Stephan Druskat

import logging

import tomlkit

from hermes.error import MisconfigurationError
from ..base import HermesCommand
from .base import HermesPostprocessPlugin


_log = logging.getLogger('postprocess.invenio_rdm')


class config_record_id(HermesPostprocessPlugin):
    def __call__(self, command: HermesCommand):
        deposition = self.get_deposit_result("invenio_rdm")

        conf = self.load(tomlkit.load, open('hermes.toml', 'r'))
        try:
            old_record_id = conf["deposit"]["invenio_rdm"]["record_id"]
            if old_record_id == deposition["record_id"]:
                return
            _log.error("hermes.toml already contains a record_id for Invenio_RDM deposit.")
            raise MisconfigurationError(
                "Can't overwrite record_id automatically."
                f"(Tried to overwrite {old_record_id} with {deposition['record_id']})"
            )
        except KeyError:
            pass
        conf.setdefault("deposit", {}).setdefault("invenio_rdm", {})["record_id"] = deposition['record_id']
        self.write(tomlkit.dump, conf, open('hermes.toml', 'w'))
