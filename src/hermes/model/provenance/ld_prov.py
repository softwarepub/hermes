# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from typing import Optional, Union
from typing_extensions import Self

from hermes import utils
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT
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
        *,
        data: EXPANDED_JSON_LD_VALUE = [{"@graph": []}],
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = PROV_DOC_IRI,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = ALL_CONTEXTS
    ) -> None:
        super().__init__([{"@graph": []}], parent=parent, key=key, index=index, context=context)

    def next_node_iri(self, type) -> str:
        if type not in ld_prov_list.INDICES:
            ld_prov_list.INDICES[type] = 0
        ld_prov_list.INDICES[type] += 1
        return self.NODE_IRI_FORMAT.format(type=type, index=ld_prov_list.INDICES[type])

    def add_activity(self, *, data={}) -> ld_dict:
        self.append(data)
        activity = self[-1]
        if "@type" not in data:
            activity["@type"] = "prov:Activity"
        else:
            activity["@type"].append("prov:Activity")
        if "@id" not in data:
            activity["@id"] = self.next_node_iri("Activity")
        return activity

    def add_agent(self, *, data={}) -> ld_dict:
        self.append(data)
        agent = self[-1]
        if "@type" not in data:
            agent["@type"] = "prov:Agent"
        else:
            agent["@type"].append("prov:Agent")
        if "@id" not in data:
            agent["@id"] = self.next_node_iri("Agent")
        return agent

    def add_entity(self, *, data={}) -> ld_dict:
        self.append(data)
        entity = self[-1]
        if "@type" not in data:
            entity["@type"] = "prov:Entity"
        else:
            entity["@type"].append("prov:Entity")
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

    def add_hermes_plugin(self, step, name) -> ld_dict:
        # TODO: add version
        node = self.add_agent(data={
            "@id": ld_prov_list.HERMES_PLUGIN_ID_FORMAT.format(step=step, name=name),
            "@type": "schema:SoftwareApplication",
            "schema:name": f"{utils.hermes_name} {step} plugin '{name}'",
            "prov:actedOnBehalfOf": self.get_hermes_base_plugin(step)
        })
        return node

    def shallow_search(self, query) -> list[ld_dict]:
        return [item for item in self if query(self, item)]

    def get_hermes(self) -> ld_dict:
        return self.shallow_search(lambda doc, node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_ID))[0]

    def get_hermes_cache(self) -> ld_dict:
        return self.shallow_search(lambda doc, node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_CACHE_ID))[0]

    def get_hermes_base_plugin(self, step) -> ld_dict:
        return self.shallow_search(lambda doc, node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_BASE_PLUGIN_ID_FORMAT.format(step=step)
        ))[0]

    def get_hermes_plugin(self, step, name) -> Union[ld_dict, None]:
        search_result = self.shallow_search(lambda doc, node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_PLUGIN_ID_FORMAT.format(step=step, name=name)
        ))
        if search_result:
            return search_result[0]
        return None

    def get_hermes_command(self, step) -> ld_dict:
        return self.shallow_search(lambda doc, node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_COMMAND_ID_FORMAT.format(step=step)
        ))[0]
