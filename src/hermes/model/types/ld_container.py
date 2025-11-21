# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from .pyld_util import JsonLdProcessor, bundled_loader

from datetime import date, time, datetime


class ld_container:
    """
    Base class for Linked Data containers.

    A linked data container impelements a view on the expanded form of an JSON-LD document.
    It allows to easily interacts them by hinding all the nesting and automatically mapping
    between different forms.
    """

    ld_proc = JsonLdProcessor()

    def __init__(self, data, *, parent=None, key=None, index=None, context=None):
        """
        Create a new instance of an ld_container.

        :param data: The expanded json-ld data that is mapped.
        :param parent: Optional parent node of this container.
        :param key: Optional key into the parent container.
        :param context: Optional local context for this container.
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
                    self.parent.active_ctx,
                    self.context,
                    {"documentLoader": bundled_loader})
            else:
                self.active_ctx = parent.active_ctx
        else:
            self.active_ctx = self.ld_proc.initial_ctx(
                self.full_context,
                {"documentLoader": bundled_loader}
            )

    def add_context(self, context):
        self.context = self.merge_to_list(self.context, context)
        self.active_ctx = self.ld_proc.process_context(
            self.active_ctx,
            context,
            {"documentLoader": bundled_loader}
        )

    @property
    def full_context(self):
        if self.parent is not None:
            return self.merge_to_list(self.parent.full_context, self.context)
        else:
            return self.context

    @property
    def path(self):
        """ Create a path representation for this item. """
        if self.parent:
            return self.parent.path + [self.key if self.index is None else self.index]
        else:
            return ['$']

    @property
    def ld_value(self):
        """ Retrun a representation that is suitable as a value in expanded JSON-LD. """
        return self._data

    def _to_python(self, full_iri, ld_value):
        if full_iri == "@id":
            value = self.ld_proc.compact_iri(self.active_ctx, ld_value, vocab=False)
        else:
            value, ld_output = self.ld_proc.apply_typemap(ld_value, "python", "ld_container",
                                                          parent=self, key=full_iri)
            if ld_output is None:
                raise TypeError(full_iri, ld_value)

        return value

    def _to_expanded_json(self, value):
        """
            The item_lists contents/ the data_dict will be substituted with value.
            Value can be an ld_container or contain zero or more.
            Then the _data of the inner most ld_dict that contains or is self will be expanded.
            If self is not an ld_dict and none of self's parents is, use the key from ld_list to generate a minimal dict

            The result of this function is what value has turned into
            (always a list for type(self) == ld_dict and list or dict for type(self) == ld_list).
            If self is an ld_list and value was assimilated by self the returned value is list otherwise it is a dict
            (e.g. in a set the inner sets values are put directly into the outer one).
        """
        if self.__class__.__name__ == "ld_list":
            value = [value]
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
        if parent.__class__.__name__ != "ld_dict":
            key = self.ld_proc.expand_iri(parent.active_ctx, parent.key)
            parent = ld_container([{key: parent._data}])
        path.append(0)

        key_and_reference_todo_list = []
        if isinstance(value, ld_container):
            if parent.__class__.__name__ == "ld_list" and parent.container_type == "@set":
                value = value._data
            else:
                value = value._data[0]
        elif isinstance(value, datetime):
            value = {"@value": value.isoformat(), "@type": "schema:DateTime"}
        elif isinstance(value, date):
            value = {"@value": value.isoformat(), "@type": "schema:Date"}
        elif isinstance(value, time):
            value = {"@value": value.isoformat(), "@type": "schema:Time"}
        else:
            key_and_reference_todo_list = [(0, [value])]
        special_types = (list, dict, ld_container, datetime, date, time)
        while True:
            if len(key_and_reference_todo_list) == 0:
                break
            key, ref = key_and_reference_todo_list.pop()
            temp = ref[key]
            if isinstance(temp, list):
                key_and_reference_todo_list.extend([(index, temp) for index, val in enumerate(temp)
                                                    if isinstance(val, special_types)])
            elif isinstance(temp, dict):
                key_and_reference_todo_list.extend([(new_key, temp) for new_key in temp.keys()
                                                    if isinstance(temp[new_key], special_types)])
            elif isinstance(temp, ld_container):
                ref[key] = temp._data[0]
            elif isinstance(temp, datetime):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:DateTime"}
            elif isinstance(temp, date):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:Date"}
            elif isinstance(temp, time):
                ref[key] = {"@value": temp.isoformat(), "@type": "schema:Time"}

        current_data = parent._data
        for index in range(len(path) - 1, 0, -1):
            current_data = current_data[path[index]]
        if current_data == []:
            self_data = None
            current_data.append(value)
        else:
            self_data = current_data[path[0]]
            current_data[path[0]] = value
        expanded_data = self.ld_proc.expand(parent._data, {"expandContext": self.full_context,
                                                           "documentLoader": bundled_loader,
                                                           "keepFreeFloatingNodes": True})
        if self_data is not None:
            current_data[path[0]] = self_data
        else:
            current_data.clear()
        for index in range(len(path) - 1, -1, -1):
            expanded_data = expanded_data[path[index]]

        if self.__class__.__name__ == "ld_dict":
            return expanded_data
        if len(expanded_data) != 1:
            return expanded_data
        return expanded_data[0]

    def _to_expanded_json_deprecated(self, key, value):
        if key == "@id":
            ld_value = self.ld_proc.expand_iri(self.active_ctx, value, vocab=False)
        elif key == "@type":
            if not isinstance(value, list):
                value = [value]
            ld_value = [self.ld_proc.expand_iri(self.active_ctx, ld_type) for ld_type in value]
        else:
            short_key = self.ld_proc.compact_iri(self.active_ctx, key)
            if ':' in short_key:
                prefix, short_key = short_key.split(':', 1)
                ctx_value = self.ld_proc.get_context_value(self.active_ctx, prefix, "@id")
                active_ctx = self.ld_proc.process_context(self.active_ctx, [ctx_value],
                                                          {"documentLoader": bundled_loader})
            else:
                active_ctx = self.active_ctx
            ld_type = self.ld_proc.get_context_value(active_ctx, short_key, "@type")
            if ld_type == "@id":
                ld_value = [{"@id": value}]
                ld_output = "expanded_json"
            else:
                ld_value, ld_output = self.ld_proc.apply_typemap(value, "expanded_json", "json",
                                                                 parent=self, key=key)
            if ld_output == "json":
                ld_value = self.ld_proc.expand(ld_value, {"expandContext": self.full_context,
                                                          "documentLoader": bundled_loader})
            elif ld_output != "expanded_json":
                raise TypeError(f"Cannot convert {type(value)}")

        return ld_value

    def __repr__(self):
        return f'{type(self).__name__}({self._data})'

    def __str__(self):
        return str(self.to_python())

    def compact(self, context=None):
        return self.ld_proc.compact(
            self.ld_value,
            context or self.context,
            {"documentLoader": bundled_loader, "skipExpand": True}
        )

    def to_python(self):
        raise NotImplementedError()

    @classmethod
    def merge_to_list(cls, *args):
        if not args:
            return []

        head, *tail = args
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
        ld_value = data[0]['@value']

        return ld_value

    @classmethod
    def are_values_equal(cls, first, second):
        if "@id" in first and "@id" in second:
            return first["@id"] == second["@id"]
        for key in {"@value", "@type"}:
            if (key in first) ^ (key in second):
                return False
            if key in first and key in second and first[key] != second[key]:
                return False
        return True
