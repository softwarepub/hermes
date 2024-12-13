# SPDX-FileCopyrightText: 2024 Helmholtz-Zentrum Dresden-Rossendorf
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileContributor: David Pape

import json
from html.parser import HTMLParser

import requests

from hermes.utils import hermes_user_agent

MARKETPLACE_URL = "https://hermes.software-metadata.pub"


class PluginMarketPlaceParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_json_ld = False
        self.plugins = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and ("type", "application/ld+json") in attrs:
            self.is_json_ld = True

    def handle_endtag(self, tag):
        self.is_json_ld = False

    def handle_data(self, data):
        if self.is_json_ld:
            linked_data = json.loads(data)
            self.plugins.append(linked_data)


def main():
    response = requests.get(MARKETPLACE_URL, headers={"User-Agent": hermes_user_agent})
    response.raise_for_status()

    parser = PluginMarketPlaceParser()
    parser.feed(response.text)

    print(
        f"See the detailed list of plugins here: {MARKETPLACE_URL}#plugins", end="\n\n"
    )

    for plugin in parser.plugins:
        name = plugin.get("name")
        where = plugin.get("url") or ("(builtin)" if plugin.get("isPartOf") else "")
        print(f"{name:>30}  {where}")


if __name__ == "__main__":
    main()
