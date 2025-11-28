# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from .pyld_util import JsonLdProcessor, bundled_loader

from datetime import date, time, datetime
from typing import Union, Self, Any


JSON_LD_CONTEXT_DICT = dict[str, Union[str, "JSON_LD_CONTEXT_DICT"]]
BASIC_TYPE = Union[str, float, int, bool]
EXPANDED_JSON_LD_VALUE = Union[
    list[Union["EXPANDED_JSON_LD_VALUE", BASIC_TYPE]], dict[str, Union["EXPANDED_JSON_LD_VALUE", BASIC_TYPE]]
]
COMPACTED_JSON_LD_VALUE = Union[
    list[Union["COMPACTED_JSON_LD_VALUE", BASIC_TYPE]], dict[str, Union["COMPACTED_JSON_LD_VALUE", BASIC_TYPE]]
]
TIME_TYPE = Union[datetime, date, time]
JSON_LD_VALUE = Union[
    list[Union["JSON_LD_VALUE", BASIC_TYPE, TIME_TYPE, "ld_container"]],
    dict[str, Union["JSON_LD_VALUE", BASIC_TYPE, TIME_TYPE, "ld_container"]],
]


class ld_container:
    """
    Base class for Linked Data containers.

    A linked data container impelements a view on the expanded form of an JSON-LD document.
    It allows to easily interacts them by hinding all the nesting and automatically mapping
    between different forms.
    """

    ld_proc = JsonLdProcessor()

    def __init__(
        self: Self,
        data: list[EXPANDED_JSON_LD_VALUE],
        *,
        parent: Union["ld_container", None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
    ) -> None:
        """
        Create a new instance of an ld_container.

        :param self: The instance of ld_container to be initialized.
        :type self: Self
        :param data: The expanded json-ld data that is mapped.
        :type data: list[EXPANDED_JSON_LD_VALUE]
        :param parent: parent node of this container.
        :type parent: ld_container | None
        :param key: key into the parent container.
        :type key: str | None
        :param index: index into the parent container.
        :type index: int | None
        :param context: local context for this container.
        :type context: list[str | JSON_LD_CONTEXT_DICT] | None

        :return:
        :rtype: None
        """
        # Store basic data
        self.parent = parent
        self.key = key
        self.index = index
        self._data = data

        self.context = context or []

        # Create active context (to use with pyld) depending on the initial variables
        # Re-use active context from parent if available
        if self.parent:
            if self.context:
                self.active_ctx = self.ld_proc.process_context(
                    self.parent.active_ctx, self.context, {"documentLoader": bundled_loader}
                )
            else:
                self.active_ctx = parent.active_ctx
        else:
            self.active_ctx = self.ld_proc.initial_ctx(self.full_context, {"documentLoader": bundled_loader})

    def add_context(self: Self, context: list[Union[str | JSON_LD_CONTEXT_DICT]]) -> None:
        """
        Add the given context to the ld_container.

        :param self: The ld_container the context should be added to.
        :type self: Self
        :param context: The context to be added to self.
        :type context: list[str | JSON_LD_CONTEXT_DICT]

        :return:
        :rtype: None
        """
        self.context = self.merge_to_list(self.context, context)
        self.active_ctx = self.ld_proc.process_context(self.active_ctx, context, {"documentLoader": bundled_loader})

    @property
    def full_context(self: Self) -> Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None]:
        """
        Return the context of the ld_container merged with the full_context of its parent.

        :param self: The ld_container whose full_context is returned
        :type self: Self

        :return: The context of the ld_container merged with the full_context of its parent via
            ld_container.merge_to_list or just the context of this ld_container if self.parent is None.
        :rtype: list[str | JSON_LD_CONTEXT_DICT] | None
        """
        if self.parent is not None:
            return self.merge_to_list(self.parent.full_context, self.context)
        else:
            return self.context

    @property
    def path(self: Self) -> list[Union[str, int]]:
        """
        Create a path representation for this item.

        :param self: The ld_container the path leads to from its outer most parent container.
        :type self: Self

        :return: The path from selfs outer most parent to it self.
            Let parent be the outer most parent of self.
            Start with index = 1 and iteratively set parent to parent[path[index]] and then increment index
            until index == len(path) to get parent is self == true.
        :rtype: list[str | int]
        """
        if self.parent:
            return self.parent.path + [self.key if self.index is None else self.index]
        else:
            return ["$"]

    @property
    def ld_value(self: Self) -> EXPANDED_JSON_LD_VALUE:
        """
        Return a representation that is suitable as a value in expanded JSON-LD of this ld_container.

        :param self: The ld_container whose expanded JSON-LD representation is returned.
        :type self: Self

        :return: The expanded JSON-LD value of this container.
            This value is the basis of all operations and a reference to the original is returned and not a copy.
            Do **not** modify unless strictly necessary and you know what you do.
            Otherwise unexpected behavior may occur.
        :rtype: EXPANDED_JSON_LD_VALUE
        """
        return self._data

    def _to_python(
        self: Self, full_iri: str, ld_value: Union[list, dict, str]
    ) -> Union["ld_container", BASIC_TYPE, TIME_TYPE]:
        """
        Returns a pythonized version of the given value pretending the value is in self and full_iri its key.

        :param self: the ld_container ld_value is considered to be in.
        :type self: Self
        :param full_iri: The expanded iri of the key of ld_value / self (later if self is not a dictionary).
        :type full_iri: str
        :param ld_value: The value thats pythonized value is requested. ld_value has to be valid expanded JSON-LD if it
            was embeded in self._data.
        :type ld_value: list | dict | str

        :return: The pythonized value of the ld_value.
        :rtype: ld_container | BASIC_TYPE | TIME_TYPE
        """
        if full_iri == "@id":
            # values of key "@id" only have to be compacted
            value = self.ld_proc.compact_iri(self.active_ctx, ld_value, vocab=False)
        else:
            # use the type map from src/hermes/model/types/__init__.py to convert all other values.
            value, ld_output = self.ld_proc.apply_typemap(ld_value, "python", "ld_container", parent=self, key=full_iri)
            # check if conversion was successful
            if ld_output is None:
                raise TypeError(full_iri, ld_value)

        return value

    def _to_expanded_json(self: Self, value: JSON_LD_VALUE) -> EXPANDED_JSON_LD_VALUE:
        """
        Returns an expanded version of the given value.

        The item_list/ data_dict of self will be substituted with value.
        Value can be an ld_container or contain zero or more.
        Then the _data of the inner most ld_dict that contains or is self will be expanded
        using the JSON_LD-Processor.
        If self and none of self's parents is an ld_dict, use the key from outer most ld_list
        to generate a minimal dict.

        The result of this function is what value has turned into.

        :param self: The ld_dict or ld_list in which value gets expanded
        :type self: Self
        :param value: The value that is to be expanded. Different types are expected based on the type of self:
            <ul><li>If type(self) == ld_dict: value must be a dict</li>
            <li>If type(self) == ld_list: value must be a list</li></ul>
            value will be exapnded as if it was the data_dict/ the item_list of self.
        :type value: JSON_LD_VALUE

        :return: The expanded version of value i.e. the data_dict/ item_list of self if it had been value.
            The return type is based on the type of self:
            <ul><li>If type(self) == ld_dict: the returned values type is dict</li>
            <li>If type(self) == ld_list: the returned values type is list</li></ul>
        :rtype: EXPANDED_JSON_LD_VALUE
        """
        # search for an ld_dict that is either self or the inner most parents parent of self that is an ld_dict
        # while searching build a path such that it leads from the found ld_dicts ld_value to selfs data_dict/ item_list
        parent = self
        path = []
        while parent.__class__.__name__ != "ld_dict":
            if parent.container_type == "@list":
                path.extend(["@list", 0])
            elif parent.container_type == "@graph":
                path.extend(["@graph", 0])
            path.append(self.ld_proc.expand_iri(parent.active_ctx, parent.key) if self.index is None else self.index)
            if parent.parent is None:
                break
            parent = parent.parent

        # if neither self nor any of its parents is a ld_dict:
        # create a dict with the key of the outer most parent of self and this parents ld_value as a value
        # this dict is stored in an ld_container and simulates the most minimal JSON-LD object possible
        if parent.__class__.__name__ != "ld_dict":
            key = self.ld_proc.expand_iri(parent.active_ctx, parent.key)
            parent = ld_container([{key: parent._data}])
        path.append(0)

        # all ld_container (ld_dicts and ld_lists) and datetime, date as well as time objects in value have to dissolved
        # because the JSON-LD processor can't handle them
        # to do this traverse value in a BFS and replace all items with a type in 'special_types' with a usable values
        key_and_reference_todo_list = [(0, [value])]
        special_types = (list, dict, ld_container, datetime, date, time)
        while True:
            # check if ready
            if len(key_and_reference_todo_list) == 0:
                break
            # get next item
            key, ref = key_and_reference_todo_list.pop()
            temp = ref[key]
            # replace item if necessary and add childs to the todo list
            if isinstance(temp, list):
                key_and_reference_todo_list.extend(
                    [(index, temp) for index, val in enumerate(temp) if isinstance(val, special_types)]
                )
            elif isinstance(temp, dict):
                key_and_reference_todo_list.extend(
                    [(new_key, temp) for new_key in temp.keys() if isinstance(temp[new_key], special_types)]
                )
            elif isinstance(temp, ld_container):
                ref[key] = temp._data[0]
            elif isinstance(temp, datetime):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:DateTime"}
            elif isinstance(temp, date):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:Date"}
            elif isinstance(temp, time):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:Time"}

        # traverse the ld_value of parent with the previously generated path
        current_data = parent._data
        for index in range(len(path) - 1, 0, -1):
            current_data = current_data[path[index]]
        # replace the data_dict/ item_list so that value is now inside of the ld_value of parent and store the old value
        if current_data == []:
            # itemlist of an empty ld_list:
            # The item_list can't be replaced like in all other cases
            self_data = None
            current_data.append(value)
        else:
            self_data = current_data[path[0]]
            current_data[path[0]] = value

        # expand the ld_value of parent to implicitly expand value
        # important the ld_value of parent is not modified because the processor makes a deep copy
        expanded_data = self.ld_proc.expand(
            parent._data,
            {"expandContext": self.full_context, "documentLoader": bundled_loader, "keepFreeFloatingNodes": True},
        )

        # restore the data_dict/ item_list to its former state
        if self_data is not None:
            current_data[path[0]] = self_data
        else:
            current_data.clear()

        # use the path to get the expansion of value
        for index in range(len(path) - 1, -1, -1):
            expanded_data = expanded_data[path[index]]

        return expanded_data

    # TODO: remove this method and all other unused methods/ functions
    def _to_expanded_json_deprecated(self, key, value):
        if key == "@id":
            ld_value = self.ld_proc.expand_iri(self.active_ctx, value, vocab=False)
        elif key == "@type":
            if not isinstance(value, list):
                value = [value]
            ld_value = [self.ld_proc.expand_iri(self.active_ctx, ld_type) for ld_type in value]
        else:
            short_key = self.ld_proc.compact_iri(self.active_ctx, key)
            if ":" in short_key:
                prefix, short_key = short_key.split(":", 1)
                ctx_value = self.ld_proc.get_context_value(self.active_ctx, prefix, "@id")
                active_ctx = self.ld_proc.process_context(
                    self.active_ctx, [ctx_value], {"documentLoader": bundled_loader}
                )
            else:
                active_ctx = self.active_ctx
            ld_type = self.ld_proc.get_context_value(active_ctx, short_key, "@type")
            if ld_type == "@id":
                ld_value = [{"@id": value}]
                ld_output = "expanded_json"
            else:
                ld_value, ld_output = self.ld_proc.apply_typemap(value, "expanded_json", "json", parent=self, key=key)
            if ld_output == "json":
                ld_value = self.ld_proc.expand(
                    ld_value, {"expandContext": self.full_context, "documentLoader": bundled_loader}
                )
            elif ld_output != "expanded_json":
                raise TypeError(f"Cannot convert {type(value)}")

        return ld_value

    def __repr__(self: Self) -> str:
        return f"{type(self).__name__}({self._data})"

    def __str__(self: Self) -> str:
        return str(self.to_python())

    def compact(
        self: Self, context: Union[list[JSON_LD_CONTEXT_DICT], JSON_LD_CONTEXT_DICT] = None
    ) -> COMPACTED_JSON_LD_VALUE:
        return self.ld_proc.compact(
            self.ld_value, context or self.context, {"documentLoader": bundled_loader, "skipExpand": True}
        )

    def to_python(self):
        raise NotImplementedError()

    @classmethod
    def merge_to_list(cls: Self, *args: tuple[Any]) -> list[Any]:
        """
        Returns a list that is contains all non-list items from args and all items in the lists in args.

        :param *args: The items that should be put into one list.
        :type *args: tuple[Any]

        :return: A list containing all non-list items and all items from lists in args. (Same order as in args)
        :rytpe: list[Any]
        """
        # base case for recursion
        if not args:
            return []

        # split args into first and all other items
        head, *tail = args
        # recursion calls
        if isinstance(head, list):
            return [*head, *cls.merge_to_list(*tail)]
        else:
            return [head, *cls.merge_to_list(*tail)]

    @classmethod
    def is_ld_node(cls, ld_value):
        return isinstance(ld_value, list) and len(ld_value) == 1 and isinstance(ld_value[0], dict)

    @classmethod
    def is_ld_id(cls, ld_value):
        return cls.is_ld_node(ld_value) and cls.is_json_id(ld_value[0])

    @classmethod
    def is_ld_value(cls, ld_value):
        return cls.is_ld_node(ld_value) and "@value" in ld_value[0]

    @classmethod
    def is_typed_ld_value(cls, ld_value):
        return cls.is_ld_value(ld_value) and "@type" in ld_value[0]

    @classmethod
    def is_json_id(cls, ld_value):
        return isinstance(ld_value, dict) and ["@id"] == [*ld_value.keys()]

    @classmethod
    def is_json_value(cls, ld_value):
        return isinstance(ld_value, dict) and "@value" in ld_value

    @classmethod
    def is_typed_json_value(cls, ld_value):
        return cls.is_json_value(ld_value) and "@type" in ld_value

    @classmethod
    def typed_ld_to_py(cls, data, **kwargs):
        ld_value = data[0]["@value"]

        return ld_value

    @classmethod
    def are_values_equal(
        cls: Self, first: dict[str, Union[BASIC_TYPE, TIME_TYPE]], second: dict[str, Union[BASIC_TYPE, TIME_TYPE]]
    ) -> bool:
        """
        Returns whether or not the given expanded JSON-LD values are considered equal.
        The comparison compares the "@id" values first and returns the result if it is conclusive.

        If the comparison is inconclusive i.e. exactly one or zero of both values have an "@id" value:
        Return whether or not all other keys exist in both values and all values of the keys are the same.

        :param first: The first value of the comparison
        :type first: dict[str, Union[BASIC_TYPE, TIME_TYPE]]
        :param second: The second value of the comparison
        :type second: dict[str, Union[BASIC_TYPE, TIME_TYPE]]

        :return: Whether the values are considered equal or not.
        :rtype: bool
        """
        # compare @id's
        if "@id" in first and "@id" in second:
            return first["@id"] == second["@id"]
        # compare all other values and keys (@id-comparison was inconclusive)
        for key in {"@value", "@type"}:
            if (key in first) ^ (key in second):
                return False
            if key in first and key in second and first[key] != second[key]:
                return False
        return True
