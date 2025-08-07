# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

from .pyld_util import JsonLdProcessor, bundled_loader


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
        elif full_iri == "@type":
            value = [
                self.ld_proc.compact_iri(self.active_ctx, ld_type)
                for ld_type in ld_value
            ]
            if len(value) == 1:
                value = value[0]
        else:
            value, ld_output = self.ld_proc.apply_typemap(ld_value, "python", "ld_container",
                                                          parent=self, key=full_iri)
            if ld_output is None:
                raise TypeError(full_iri, ld_value)

        return value

    def _to_expanded_json(self, key, value):
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
        return f'{type(self).__name__}({self._data[0]})'

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
