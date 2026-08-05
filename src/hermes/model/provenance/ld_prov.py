# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from importlib.metadata import metadata
from typing import Optional, Union
from typing_extensions import Self

from hermes import utils
from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import BASIC_TYPE, EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT
from hermes.model.types.ld_context import ALL_CONTEXTS, iri_map


class ld_prov_list(ld_list):
    NODE_IRI_FORMAT = "_:{type}/{index}"
    HERMES_ID = f"https://doi.org/{utils.hermes_doi}"
    HERMES_CACHE_ID = "_:hermes/cache"
    HERMES_COMMAND_ID_FORMAT = "_:hermes/command/{step}"
    HERMES_PLUGIN_ID_FORMAT = "_:hermes/plugin/{step}/{name}"
    HERMES_BASE_PLUGIN_ID_FORMAT = "_:hermes/base_plugin/{step}"
    PROV_DOC_IRI = iri_map['hermes-rt', "graph"]
    INDICES = {}

    def __init__(
        self: Self,
        data: EXPANDED_JSON_LD_VALUE = [{"@graph": []}],
        *,
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = PROV_DOC_IRI,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = ALL_CONTEXTS
    ) -> None:
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    @classmethod
    def load_ld_prov_list(cls, data) -> "ld_prov_list":
        if cls.INDICES != {}:
            raise RuntimeError("Only zero or one objects of class 'ld_prov_list' may exist at every point in time.")
        prov_list = cls.from_list(
            data[0]["@graph"], key=cls.PROV_DOC_IRI, context=ALL_CONTEXTS, container_type="@graph"
        )
        for item in prov_list:
            if not ("@id" in item and item["@id"].startswith("_:")):
                continue
            item_id = item["@id"][2:].split("/")
            if not (len(item_id) == 2 and item_id[1].isnumeric()):
                continue
            if cls.INDICES.get(item_id[0], 0) < int(item_id[1]):
                cls.INDICES[item_id[0]] = int(item_id[1])
        return prov_list

    def next_node_iri(self, type) -> str:
        if type not in ld_prov_list.INDICES:
            ld_prov_list.INDICES[type] = 0
        ld_prov_list.INDICES[type] += 1
        return self.NODE_IRI_FORMAT.format(type=type, index=ld_prov_list.INDICES[type])

    def add_activity(self, *, data={}) -> ld_dict:
        self.append(data)
        activity = self[-1]
        if "@type" not in data:
            activity["@type"] = ["prov:Activity", "schema:Action"]
        else:
            activity["@type"].extend(["prov:Activity", "schema:Action"])
        if "@id" not in data:
            activity["@id"] = self.next_node_iri("Activity")
        return activity

    def add_agent(self, *, data={}) -> ld_dict:
        self.append(data)
        agent = self[-1]
        if "@type" not in data:
            agent["@type"] = ["prov:Agent", "schema:SoftwareApplication"]
        else:
            agent["@type"].extend(["prov:Agent", "schema:SoftwareApplication"])
        if "@id" not in data:
            agent["@id"] = self.next_node_iri("Agent")
        return agent

    def add_entity(self, *, data={}) -> ld_dict:
        self.append(data)
        entity = self[-1]
        if "@type" not in data:
            entity["@type"] = ["prov:Entity", "schema:Thing"]
        else:
            entity["@type"].extend(["prov:Entity", "schema:Thing"])
        if "@id" not in data:
            entity["@id"] = self.next_node_iri("Entity")
        return entity

    def init_hermes_agents(self) -> None:
        hermes = self.add_agent(data={
            "@id": ld_prov_list.HERMES_ID,
            "@type": "schema:SoftwareApplication",
            "schema:name": utils.hermes_name,
            "schema:version": utils.hermes_version,
            "schema:url": [*set(utils.hermes_urls.values())]
        })
        self.add_agent(data={
            "@id": ld_prov_list.HERMES_CACHE_ID,
            "@type": "schema:SoftwareApplication",
            "schema:name": utils.hermes_name + " cache",
            "schema:version": utils.hermes_version,
            "prov:actedOnBehalfOf": hermes.ref
        })
        for step in ["harvest", "process", "curate", "deposit", "postprocess"]:
            command = self.add_agent(data={
                "@id": ld_prov_list.HERMES_COMMAND_ID_FORMAT.format(step=step),
                "@type": "schema:SoftwareApplication",
                "schema:name": f"{utils.hermes_name} {step} command",
                "schema:version": utils.hermes_version,
                "prov:actedOnBehalfOf": hermes.ref
            })
            self.add_agent(data={
                "@id": ld_prov_list.HERMES_BASE_PLUGIN_ID_FORMAT.format(step=step),
                "@type": "schema:SoftwareApplication",
                "schema:name": f"{utils.hermes_name} {step} base plugin",
                "schema:version": utils.hermes_version,
                "prov:actedOnBehalfOf": command.ref
            })

    def add_hermes_settings(self, command: HermesCommand) -> None:
        hermes = self.get_hermes()
        hermes.emplace("schema:supportingData")
        hermes["schema:supportingData"].append({
            "@type": "schema:DataFeed",
            "schema:dataFeedElement": [
                {
                    "@type": "schema:DataFeedItem",
                    "schema:name": name,
                    "schema:item": [
                        {
                            "@type": "schema:Item",
                            "schema:description": value
                        }
                    ],
                    "schema:description": "setting provided by command line (or its default value)"
                }
                for name, value in [
                    ("path", command.args.path.absolute().as_uri()),
                    ("config", command.args.config.absolute().as_uri()),
                    ("options", str(command.args.options))
                ]
            ],
            "schema:description": f"options for run {len(hermes['schema:supportingData']) + 1} of some hermes step"
        })
        for name, values in command.root_settings.model_dump(mode="json").items():
            if not isinstance(values, list):
                values = [values]
            hermes["schema:supportingData"][-1]["schema:dataFeedElement"].append({
                "@type": "schema:DataFeedItem",
                "schema:name": name,
                "schema:item": [
                    {
                        "@type": "schema:Item",
                        "schema:description": value
                    }
                    for value in values
                ],
                "schema:description": "setting loaded from the config file"
            })

    def add_settings_to_command(self, step: str, command: HermesCommand) -> None:
        command_prov = self.get_hermes_command(step)
        command_prov.emplace("schema:supportingData")
        command_prov["schema:supportingData"].append({
            "@type": "schema:DataFeed",
            "schema:dataFeedElement": [],
            "schema:description": f"options for run {len(command_prov['schema:supportingData']) + 1} of step {step} out"
                                  f" of {len(self.get_hermes()['schema:supportingData'])} runs of some hermes step"
        })  # Needs add_hermes_settings to be called before add_settings_to_command is called!
        for name, values in command.settings.model_dump(mode="json").items():
            if not isinstance(values, list):
                values = [values]
            command_prov["schema:supportingData"][-1]["schema:dataFeedElement"].append({
                "@type": "schema:DataFeedItem",
                "schema:name": name,
                "schema:item": [
                    {
                        "@type": "schema:Item",
                        "schema:description": value
                    }
                    for value in values
                ]
            })

    def add_hermes_plugin(self, step: str, name: str, plugin: HermesPlugin, command: HermesCommand) -> ld_dict:
        data = {
            "@id": ld_prov_list.HERMES_PLUGIN_ID_FORMAT.format(step=step, name=name),
            "@type": "schema:SoftwareApplication",
            "schema:name": f"{plugin.__module__}.{plugin.__class__.__qualname__}",
            "schema:description": f"{utils.hermes_name} {step} plugin '{name}'",
            "schema:supportingData": {
                "@type": "schema:DataFeed",
                "schema:dataFeedElement": []
            },
            "prov:actedOnBehalfOf": self.get_hermes_base_plugin(step).ref
        }
        try:
            for name, values in getattr(command.settings, name).model_dump(mode="json").items():
                if not isinstance(values, list):
                    values = [values]
                data["schema:supportingData"]["schema:dataFeedElement"].append({
                    "@type": "schema:DataFeedItem",
                    "schema:name": name,
                    "schema:item": [
                        {
                            "@type": "schema:Item",
                            "schema:description": value
                        }
                        for value in values
                    ]
                })
        except Exception:
            del data["schema:supportingData"]
        try:
            data["schema:softwareVersion"] = metadata(plugin.__module__)["version"]
        except Exception:
            pass
        node = self.add_agent(data=data)
        return node

    def shallow_search(self, query) -> list[ld_dict]:
        return [item for item in self if query(item)]

    def get_hermes(self) -> ld_dict:
        return self.shallow_search(lambda node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_ID))[0]

    def get_hermes_cache(self) -> ld_dict:
        return self.shallow_search(lambda node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_CACHE_ID))[0]

    def get_hermes_base_plugin(self, step) -> ld_dict:
        return self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_BASE_PLUGIN_ID_FORMAT.format(step=step)
        ))[0]

    def get_hermes_plugin(self, step, name) -> Union[ld_dict, None]:
        search_result = self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_PLUGIN_ID_FORMAT.format(step=step, name=name)
        ))
        if search_result:
            return search_result[0]
        return None

    def get_hermes_command(self, step) -> ld_dict:
        return self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_COMMAND_ID_FORMAT.format(step=step)
        ))[0]
