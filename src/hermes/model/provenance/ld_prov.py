# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from typing import Optional, Union
from typing_extensions import Self
import uuid

from hermes import utils
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import BASIC_TYPE, EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT, TIME_TYPE
from hermes.model.types.ld_context import ALL_CONTEXTS, iri_map


class ld_prov_container:
    def _to_python(
        self: Self,
        full_iri: str,
        ld_value: Union[EXPANDED_JSON_LD_VALUE, dict[str, EXPANDED_JSON_LD_VALUE], list[str], str]
    ) -> Union["ld_prov_node", "ld_prov_list", BASIC_TYPE, TIME_TYPE]:
        item = super()._to_python(full_iri, ld_value)
        if isinstance(item, ld_list):
            return ld_prov_list(
                data=item._data, parent=item.parent, key=item.key, index=item.index, context=item.context
            )
        elif isinstance(item, ld_dict):
            return ld_prov_node(
                data=item._data, parent=item.parent, key=item.key, index=item.index, context=item.context
            )
        return item


class ld_prov_list(ld_list):
    NODE_IRI_FORMAT = "graph://{uuid}/{index}"
    PROV_DOC_IRI = iri_map['hermes-rt', "graph"]

    def __init__(
        self: Self,
        *,
        data: EXPANDED_JSON_LD_VALUE = [{"@graph": []}],
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = PROV_DOC_IRI,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = ALL_CONTEXTS
    ) -> None:
        self.id = uuid.uuid1()
        self.node_index = 0
        super().__init__([{"@graph": []}], parent=parent, key=key, index=index, context=context)

    def __getitem__(
        self: Self, index: Union[int, slice]
    ) -> Union[
        BASIC_TYPE,
        TIME_TYPE,
        "ld_prov_node",
        "ld_prov_list",
        list[Union[BASIC_TYPE, TIME_TYPE, "ld_prov_node", "ld_prov_list"]]
    ]:
        item = super().__getitem__(index)
        if isinstance(item, ld_list):
            return ld_prov_list(
                data=item._data, parent=item.parent, key=item.key, index=item.index, context=item.context
            )
        elif isinstance(item, ld_dict):
            return ld_prov_node(
                data=item._data, parent=item.parent, key=item.key, index=item.index, context=item.context
            )
        return item

    def next_node_iri(self) -> str:
        self.node_index += 1
        return self.NODE_IRI_FORMAT.format(uuid=self.id, index=self.node_index)

    def add_activity(self) -> "ld_prov_node":
        self.append({"@id": self.next_node_iri(), "@type": "prov:Activity"})
        return self[-1]

    def add_agent(self) -> "ld_prov_node":
        self.append({"@id": self.next_node_iri(), "@type": "prov:Agent"})
        return self[-1]

    def add_entity(self) -> "ld_prov_node":
        self.append({"@id": self.next_node_iri(), "@type": "prov:Entity"})
        return self[-1]

    def init_hermes_agents(self) -> "ld_prov_node":
        hermes = self.add_agent()
        hermes.update({
            "schema:name": utils.hermes_name,
            "schema:version": utils.hermes_version,
            "schema:url": utils.hermes_urls,
        })
        hermes["@type"].append("schema:SoftwareApplication")
        node = self.add_agent()
        node.update({
            "schema:name": utils.hermes_name + " cache",
            "schema:version": utils.hermes_version,
            "prov:actedOnBehalfOf": hermes.ref
        })
        node["@type"].append("schema:SoftwareApplication")
        return node

    def add_hermes_command(self, step) -> "ld_prov_node":
        node = self.add_agent()
        node.update({
            "schema:name": f"{utils.hermes_name} {step} command",
            "schema:version": utils.hermes_version,
            "prov:actedOnBehalfOf": self.shallow_search(
                {"schema:name": (lambda doc, node: node["schema:name"] == utils.hermes_name)}
            )
        })
        node["@type"].append("schema:SoftwareApplication")
        return node

    def add_hermes_base_plugin(self, step) -> "ld_prov_node":
        node = self.add_agent()
        node.update({
            "schema:name": f"{utils.hermes_name} {step} base plugin",
            "schema:version": utils.hermes_version,
            "prov:actedOnBehalfOf": self.shallow_search(
                {"schema:name": (lambda doc, node: node["schema:name"] == f"{utils.hermes_name} {step} command")}
            )
        })
        node["@type"].append("schema:SoftwareApplication")
        return node

    def add_hermes_plugin(self, step, name) -> "ld_prov_node":
        node = self.add_agent()
        # TODO: add version
        node.update({
            "schema:name": f"{utils.hermes_name} {step} plugin '{name}'",
            "prov:actedOnBehalfOf": self.shallow_search(
                {"schema:name": (lambda doc, node: node["schema:name"] == f"{utils.hermes_name} {step} base plugin")}
            )
        })
        node["@type"].append("schema:SoftwareApplication")
        return node

    def shallow_search(self, query: dict) -> list["ld_prov_node"]:
        return [
            item for item in self for key, test in query.items() if key in item and test(self, item)
        ]


class ld_prov_node(ld_dict):
    def __init__(
        self: Self,
        data: list[dict[str, EXPANDED_JSON_LD_VALUE]],
        *,
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = None,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = ALL_CONTEXTS
    ) -> None:
        self.id = uuid.uuid1()
        super().__init__(data, parent=parent, key=key, index=index, context=context)
