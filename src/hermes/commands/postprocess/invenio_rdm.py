# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import logging

import toml

from hermes.commands.base import HermesCommand
from hermes.error import MisconfigurationError
from hermes.model.context_manager import HermesContext

from .base import HermesPostprocessPlugin

_log = logging.getLogger('postprocess.invenio_rdm')


class config_record_id(HermesPostprocessPlugin):
    def __call__(self, command: HermesCommand):
        ctx = HermesContext()
        ctx.prepare_step("deposit")
        with ctx["invenio_rdm"] as manager:
            deposition = manager["result"]
        ctx.finalize_step("deposit")

        conf = toml.load(open('hermes.toml', 'r'))
        try:
            old_record_id = conf["deposit"]["invenio_rdm"]["record_id"]
            if old_record_id == deposition["record_id"]:
                return
            _log.error("hermes.toml already contains a record_id for Invenio_RDM deposit.")
            raise MisconfigurationError(
                "Can't overwrite record_id automatically."
                f"(Tried to overwrite {old_record_id} with {deposition["record_id"]})"
            )
        except KeyError:
            pass
        conf.setdefault("deposit", {}).setdefault("invenio_rdm", {})["record_id"] = deposition['record_id']
        toml.dump(conf, open('hermes.toml', 'w'))
