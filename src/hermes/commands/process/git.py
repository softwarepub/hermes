# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat

import logging
import pathlib

from hermes.model.context import CodeMetaContext, HermesHarvestContext, ContextPath


audit_log = logging.getLogger("audit.git")


def add_contributors(
    path: pathlib.Path,
    config_path: pathlib.Path,
    ctx: CodeMetaContext,
    harvest_ctx: HermesHarvestContext,
):
    """
    Add all git authors and committers with role `Contributor`.

    :param path: The working path
    :param config_path: The path of the config TOML file
    :param ctx: The target context containing harmonized data
    :param harvest_ctx: Data as it was harvested
    """
    audit_log.info("")
    audit_log.info("### Add git authors and committers as contributors")

    contributor_path = ContextPath("contributor")

    tags = {}
    try:
        data = harvest_ctx.get_data(tags=tags)
    except ValueError:
        audit_log.info("- Inconsistent data, skipping.")
        return

    for i, contributor in enumerate(contributor_path.get_from(data)):
        audit_log.debug("- %s", contributor["name"])
        if contributor_path not in ctx.keys():
            ctx.update(contributor_path, [])
        ctx.update(contributor_path["*"], contributor, tags=tags)

    ctx.tags.update(tags)


def add_branch(
    path: pathlib.Path,
    config_path: pathlib.Path,
    ctx: CodeMetaContext,
    harvest_ctx: HermesHarvestContext,
):
    """
    Add the git branch.

    :param path: The working path
    :param config_path: The path of the config TOML file
    :param ctx: The target context containing harmonized data.
    :param harvest_ctx: Data as it was harvested.
    """
    audit_log.info("")
    audit_log.info("### Add git branch")

    branch_path = ContextPath("hermes:gitBranch")

    tags = {}
    try:
        data = harvest_ctx.get_data(tags=tags)
    except ValueError:
        audit_log.info("- Inconsistent data, skipping.")
        return

    branch = branch_path.get_from(data)
    audit_log.debug("- %s", branch)
    ctx.update(branch_path, branch, tags=tags)

    ctx.tags.update(tags)


def process(
    path: pathlib.Path,
    config_path: pathlib.Path,
    ctx: CodeMetaContext,
    harvest_ctx: HermesHarvestContext,
):
    """
    Process harvested Git metadata

    :param path: The working path
    :param config_path: The path of the config TOML file
    :param ctx: The target context containing harmonized data.
    :param harvest_ctx: Data as it was harvested.
    """
    add_contributors(path, config_path, ctx, harvest_ctx)
    add_branch(path, config_path, ctx, harvest_ctx)
    harvest_ctx.finish()
