import json
from pathlib import Path
from typing import Any, Dict

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


def plugin_to_jsonld(obj: Dict[str, Any]) -> Dict[str, Any]:
    data = {
        "@context": "https://schema.org/",
        "@type": "SoftwareApplication",
    }

    basic_mapping = {
        "name": "name",
        "url": "repository_url",
        "installUrl": "pypi_url",
        "abstract": "description",
    }
    for schema_name, our_name in basic_mapping.items():
        if (value := obj.get(our_name)) is not None:
            data[schema_name] = value

    if (author := obj.get("author")) is not None:
        data["author"] = {"@type": "Organization", "name": author}

    keywords = []

    for step in obj.get("steps", []):
        keywords.append(f"hermes-step-{step}")

    data["keywords"] = keywords
    return data


class PluginMarkupDirective(SphinxDirective):
    required_arguments = 1

    def run(self) -> list[nodes.Node]:
        plugins_file_path = self.arguments[0]
        filename, _linenumber = self.get_source_info()

        plugins_file = Path(filename).parent / Path(plugins_file_path)
        with open(plugins_file) as file:
            plugin_data = json.load(file)

        tags = []
        for plugin in plugin_data:
            markup = plugin_to_jsonld(plugin)
            tag = f'<script type="application/ld+json">{json.dumps(markup)}</script>'
            tags.append(nodes.raw(rawsource=markup, text=tag, format="html"))

        return tags


def setup(app: Sphinx):
    app.add_directive("plugin-markup", PluginMarkupDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
