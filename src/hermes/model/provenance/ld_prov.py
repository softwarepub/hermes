# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

from importlib.metadata import metadata
from typing import Any, Callable, Optional, Union
from typing_extensions import Self

from hermes import utils
from hermes.commands.base import HermesCommand, HermesPlugin
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import EXPANDED_JSON_LD_VALUE, JSON_LD_CONTEXT_DICT, JSON_LD_VALUE
from hermes.model.types.ld_context import ALL_CONTEXTS, iri_map


class ld_prov_list(ld_list):
    """
    ld_list with special features for internal provenance collection.

    Attributes:
        NODE_IRI_FORMAT (str): (class attribute) The id format of normal nodes.
        HERMES_ID (str): (class attribute) The id of the hermes agent.
        HERMES_CACHE_ID (str): (class attribute) The id of the hermes cache.
        HERMES_COMMAND_ID_FORMAT (str): (class attribute) The id format of hermes commands.
        HERMES_PLUGIN_ID_FORMAT (str): (class attribute) The id format of hermes plugins.
        HERMES_BASE_PLUGIN_ID_FORMAT (str): (class attribute) The id format of hermes base plugins.
        PROV_DOC_IRI (str): (class attribute) The JSON-LD type of the prov_doc itself.
        INDICES (dict[str, int]): (class attribute) The counters of the different types of nodes.
    """
    NODE_IRI_FORMAT: str = "_:{type}/{index}"
    HERMES_ID: str = f"https://doi.org/{utils.hermes_doi}"
    HERMES_CACHE_ID: str = "_:hermes/cache"
    HERMES_COMMAND_ID_FORMAT: str = "_:hermes/command/{step}"
    HERMES_PLUGIN_ID_FORMAT: str = "_:hermes/plugin/{step}/{name}"
    HERMES_BASE_PLUGIN_ID_FORMAT: str = "_:hermes/base_plugin/{step}"
    PROV_DOC_IRI: str = iri_map['hermes-rt', "graph"]
    INDICES: dict[str, int] = {}

    def __init__(
        self: Self,
        data: EXPANDED_JSON_LD_VALUE = [{"@graph": []}],
        *,
        parent: Optional[Union[ld_dict, ld_list]] = None,
        key: Optional[str] = PROV_DOC_IRI,
        index: Optional[int] = None,
        context: Optional[list[Union[str, JSON_LD_CONTEXT_DICT]]] = ALL_CONTEXTS
    ) -> None:
        """
        Create a new instance of an ld_prov_list, should not be used.
        Use :meth:`ld_prov_list.load_ld_prov_list` instead.
        See also :meth:`ld_list.__init__`.

        Args:
            data (EXPANDED_JSON_LD_VALUE): The expanded json-ld data that represents the list, default is an empty graph
            parent (ld_dict | ld_list | None): parent node of this container.
            key (str | None): key into the parent container.
            index (int | None): index into the parent container.
            context (list[str | JSON_LD_CONTEXT_DICT] | None): local context for this container.

        Returns:
            None:
        """
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    @classmethod
    def load_ld_prov_list(cls: type[Self], data: EXPANDED_JSON_LD_VALUE) -> "ld_prov_list":
        """
        Create a new instance of an ld_merge_dict. See also :meth:`ld_dict.__init__`.

        Args:
            data (EXPANDED_JSON_LD_VALUE): The expanded json-ld data from which an ld_prov_list is restored.

        Returns:
            ld_prov_list: The ld_prov_list loaded from the provided data.

        Raises:
            RuntimeError: If an ld_prov_list has/ had been loaded before.
        """
        # check if an ld_prov_list has/ had been loaded before
        if cls.INDICES != {}:
            raise RuntimeError("Only zero or one objects of class 'ld_prov_list' may exist at every point in time.")
        # create ld_prov_list from the data
        prov_list = cls.from_list(
            data[0]["@graph"], key=cls.PROV_DOC_IRI, context=ALL_CONTEXTS, container_type="@graph"
        )
        # initialize counters for different node types
        for item in prov_list:
            if not ("@id" in item and item["@id"].startswith("_:")):
                continue
            item_id = item["@id"][2:].split("/")
            if not (len(item_id) == 2 and item_id[1].isnumeric()):
                continue
            if cls.INDICES.get(item_id[0], 0) < int(item_id[1]):
                cls.INDICES[item_id[0]] = int(item_id[1])
        return prov_list

    def next_node_iri(self: Self, type: str) -> str:
        """
        Create an iri for a new node of the given type.

        Args:
            type (str): The type of the new node

        Returns:
            str: The generated iri.
        """
        # update counter for the given type
        if type not in ld_prov_list.INDICES:
            ld_prov_list.INDICES[type] = 0
        ld_prov_list.INDICES[type] += 1
        # generate and return the iri
        return self.NODE_IRI_FORMAT.format(type=type, index=ld_prov_list.INDICES[type])

    def add_activity(self: Self, *, data: JSON_LD_VALUE = {}) -> ld_dict:
        """
        Add a new provenance activity to the ld_prov_list using the provided additional data.

        Hint: If no id was specified, one will be generated. Additionaly the types 'prov:Activity' and
        'schema:Action' will be added.

        Args:
            data (JSON_LD_VALUE): The additional data for the activity.

        Returns:
            ld_dict: The provenance activity as an ld_dict (can be used to update the data in the ld_prov_list).
        """
        # add and get the object
        self.append(data)
        activity = self[-1]
        # add the additional types
        if "@type" not in data:
            activity["@type"] = ["prov:Activity", "schema:Action"]
        else:
            activity["@type"].extend(["prov:Activity", "schema:Action"])
        # add an id if necessary
        if "@id" not in data:
            activity["@id"] = self.next_node_iri("Activity")
        # return the object
        return activity

    def add_agent(self: Self, *, data: JSON_LD_VALUE = {}) -> ld_dict:
        """
        Add a new provenance agent to the ld_prov_list using the provided additional data.

        Hint: If no id was specified, one will be generated. Additionaly the types 'prov:Agent' and
        'schema:SoftwareApplication' will be added.

        Args:
            data (JSON_LD_VALUE): The additional data for the agent.

        Returns:
            ld_dict: The provenance agent as an ld_dict (can be used to update the data in the ld_prov_list).
        """
        # add and get the object
        self.append(data)
        agent = self[-1]
        # add the additional types
        if "@type" not in data:
            agent["@type"] = ["prov:Agent", "schema:SoftwareApplication"]
        else:
            agent["@type"].extend(["prov:Agent", "schema:SoftwareApplication"])
        # add an id if necessary
        if "@id" not in data:
            agent["@id"] = self.next_node_iri("Agent")
        # return the object
        return agent

    def add_entity(self: Self, *, data: JSON_LD_VALUE = {}) -> ld_dict:
        """
        Add a new provenance entity to the ld_prov_list using the provided additional data.

        Hint: If no id was specified, one will be generated. Additionaly the types 'prov:Entity' and
        'schema:Thing' will be added.

        Args:
            data (JSON_LD_VALUE): The additional data for the entity.

        Returns:
            ld_dict: The provenance entity as an ld_dict (can be used to update the data in the ld_prov_list).
        """
        # add and get the object
        self.append(data)
        entity = self[-1]
        # add the additional types
        if "@type" not in data:
            entity["@type"] = ["prov:Entity", "schema:Thing"]
        else:
            entity["@type"].extend(["prov:Entity", "schema:Thing"])
        # add an id if necessary
        if "@id" not in data:
            entity["@id"] = self.next_node_iri("Entity")
        # return the object
        return entity

    def init_hermes_agents(self: Self) -> None:
        """
        Initialize the hermes agents for provenance collection.

        Returns:
            None:
        """
        # add an agent for both hermes itself and the hermes cache
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
        # add the agents for each command and base plugin
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

    def add_hermes_settings(self: Self, command: HermesCommand) -> None:
        """
        Add general settings of a hermes command run from the command object.

        Args:
            command (HermesCommand): The command object containing information on the run.

        Returns:
            None:
        """
        # add basic settings
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
        # add command specific settings
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

    def add_settings_to_command(self: Self, step: str, command: HermesCommand) -> None:
        """
        Add settings specific to the ran command from the command object.
        :meth:`ld_prov_list.add_hermes_settings` must be run before this function.

        Args:
            step (str): The step of the settings should be recorded for.
            command (HermesCommand): The command object containing information on the run.

        Returns:
            None:
        """
        # add basics
        command_prov = self.get_hermes_command(step)
        command_prov.emplace("schema:supportingData")
        command_prov["schema:supportingData"].append({
            "@type": "schema:DataFeed",
            "schema:dataFeedElement": [],
            "schema:description": f"options for run {len(command_prov['schema:supportingData']) + 1} of step {step} out"
                                  f" of {len(self.get_hermes()['schema:supportingData'])} runs of some hermes step"
        })  # Needs add_hermes_settings to be called before add_settings_to_command is called!
        # add specific settings to the command
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

    def add_hermes_plugin(self: Self, step: str, name: str, plugin: HermesPlugin, command: HermesCommand) -> ld_dict:
        """
        Add a new hermes plugin to the ld_prov_list using the provided additional data.

        Args:
            step (str): The step of the plugin.
            name (str): The name of the plugin.
            plugin (HermesPlugin): The object of the plugin that will be executed.
            command (HermesCommand): The command object containing information on the run.

        Returns:
            ld_dict: The provenance entity of the plugin (can be used to update the data in the ld_prov_list).
        """
        # construct basic data dict
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
        # try adding the settings for the plugin
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
        # try adding the version of the package of the plugin
        try:
            data["schema:softwareVersion"] = metadata(plugin.__module__.split(".")[0])["version"]
        except Exception:
            pass
        # add the plugin to the ld_prov_list and return the object
        node = self.add_agent(data=data)
        return node

    def shallow_search(self: Self, query: Callable[[ld_dict], Any]) -> list[ld_dict]:
        """
        Search the objects in the ld_prov_list for objects for which the query evaluates to True.

        Args:
            query (Callable[[ld_dict], Any]): The query used for evaluating the objects.

        Returns:
            list[ld_dict]: The objects in the ld_prov_list for which `query` evalutes to True.
        """
        return [item for item in self if query(item)]

    def get_hermes(self: Self) -> ld_dict:
        """
        Returns the hermes agent in the ld_prov_list.

        Returns:
            ld_dict: The object representing the hermes agent.
        """
        return self.shallow_search(lambda node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_ID))[0]

    def get_hermes_cache(self: Self) -> ld_dict:
        """
        Returns the hermes cache agent in the ld_prov_list.

        Returns:
            ld_dict: The object representing the hermes cache agent.
        """
        return self.shallow_search(lambda node: ("@id" in node and node["@id"] == ld_prov_list.HERMES_CACHE_ID))[0]

    def get_hermes_base_plugin(self: Self, step: str) -> ld_dict:
        """
        Returns the base plugin agent in the ld_prov_list of the given step.

        Args:
            step (str): The step of which the base plugin agent should be returned.

        Returns:
            ld_dict: The object representing the base plugin agent of the given step.
        """
        return self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_BASE_PLUGIN_ID_FORMAT.format(step=step)
        ))[0]

    def get_hermes_plugin(self: Self, step: str, name: str) -> Union[ld_dict, None]:
        """
        Returns the plugin agent in the ld_prov_list of the given step with the given name.

        Args:
            step (str): The step of which the plugin agent should be returned.
            name (str): The name of the plugin agent that should be returned.

        Returns:
            ld_dict | None: The object representing the plugin agent of the given step with the given name.
        """
        search_result = self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_PLUGIN_ID_FORMAT.format(step=step, name=name)
        ))
        if search_result:
            return search_result[0]
        return None

    def get_hermes_command(self, step) -> ld_dict:
        """
        Returns the hermes command agent in the ld_prov_list of the given step.

        Args:
            step (str): The step of which the hermes command agent should be returned.

        Returns:
            ld_dict: The object representing the hermes command agent of the given step.
        """
        return self.shallow_search(lambda node: (
            "@id" in node and node["@id"] == ld_prov_list.HERMES_COMMAND_ID_FORMAT.format(step=step)
        ))[0]
