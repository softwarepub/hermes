# SPDX-FileCopyrightText: 2023 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import json
import logging

import toml


_log = logging.getLogger('deposit.invenio_rdm')


def config_record_id(ctx):
    deposition_path = ctx.get_cache('deposit', 'deposit')
    with deposition_path.open("r") as deposition_file:
        deposition = json.load(deposition_file)
    conf = ctx.config.hermes
    try:
        conf['deposit']['invenio_rdm']['record_id'] = deposition['record_id']
        toml.dump(conf, open('hermes.toml', 'w'))
    except KeyError:
        raise RuntimeError("No deposit.invenio configuration available to store record id in") from None
