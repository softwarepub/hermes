# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

import json
from pathlib import Path
from typing import Any, Dict

from docutils import nodes
from jsonschema import validate
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.console import colorize
from sphinx.util.docutils import SphinxDirective

from hermes.commands.marketplace import (
    SchemaOrgOrganization,
    SchemaOrgSoftwarePublication,
    schema_org_hermes,
)


logger = logging.getLogger(__name__)


def log_message(text: str, text2: str = None) -> None:
    message = colorize("bold", "[Plugin Markup]") + " " + text
    if text2 is not None:
        message += " " + colorize("darkgreen", text2)
    logger.info(message)


def plugin_to_schema_org(plugin: Dict[str, Any]) -> SchemaOrgSoftwarePublication:
    """Convert plugin metadata from the used JSON format to Schema.org.

    The ``plugin`` is transformed into a ``schema:SoftwareApplication``. For most
    attributes of the plugin, a mapping into Schema.org terms is performed. The author
    is expressed as a ``schema:Organization`` using the given author field as the
    ``name``. The steps targeted by the plugin are expressed using the ``keyword`` field
    by transforming them to the keywords ``hermes-step-<STEP>`` where ``<STEP>`` is the
    name of the workflow step. If the plugin is marked as a Hermes ``builtin``, this is
    expressed using ``schema:isPartOf``.
    """
    keywords = [f"hermes-step-{step}" for step in plugin.get("steps", [])]

    return SchemaOrgSoftwarePublication(
        name=plugin.get("name"),
        url=plugin.get("repository_url"),
        install_url=plugin.get("pypi_url"),
        abstract=plugin.get("description"),
        author=SchemaOrgOrganization(name=au) if (au := plugin.get("author")) else None,
        is_part_of=schema_org_hermes if plugin.get("builtin", False) else None,
        keywords=keywords or None,
    )


class PluginMarkupDirective(SphinxDirective):
    """A Sphinx directive to render the ``plugins.json`` file to Schema.org markup.

    The plugins file is passed to the directive as the first parameter, i.e., in
    Markdown:

    .. code:: markdown

       ```{plugin-markup} path/to/plugins.json path/to/plugins-schema.json
       ```

    For each plugin listed in the file, a ``<script type="application/ld+json">`` tag
    is generated.
    """

    required_arguments = 2

    def run(self) -> list[nodes.Node]:
        filename = Path(self.get_source_info()[0])  # currently processing this file
        directory = filename.parent

        plugins_file = directory / self.arguments[0]
        log_message("reading plugins file", text2=str(plugins_file))
        with open(plugins_file) as file:
            plugin_data = json.load(file)

        plugins_schema_file = directory / self.arguments[1]
        log_message("reading plugins schema file", text2=str(plugins_schema_file))
        with open(plugins_schema_file) as file:
            plugin_schema = json.load(file)

        log_message("validating plugins")
        validate(plugin_data, plugin_schema)

        log_message("converting plugins to markup")
        tags = []
        for plugin in plugin_data:
            markup = plugin_to_schema_org(plugin).model_dump_json(
                by_alias=True, exclude_none=True
            )
            tag = f'<script type="application/ld+json">{markup}</script>'
            tags.append(nodes.raw(rawsource=markup, text=tag, format="html"))

        return tags


def setup(app: Sphinx):
    """Wire up the directive so that it can be used as ``plugin-markup``."""
    app.add_directive("plugin-markup", PluginMarkupDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
