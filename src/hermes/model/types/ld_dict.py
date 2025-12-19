# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from .ld_container import ld_container

from .pyld_util import bundled_loader


class ld_dict(ld_container):
    _NO_DEFAULT = type("NO DEFAULT")

    def __init__(self, data, *, parent=None, key=None, index=None, context=None):
        if not self.is_ld_dict(data):
            raise ValueError("The given data does not represent a ld_dict.")
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        self.data_dict = data[0]

    def __getitem__(self, key):
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        ld_value = self.data_dict[full_iri]
        return self._to_python(full_iri, ld_value)

    def __setitem__(self, key, value):
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        ld_value = self._to_expanded_json({full_iri: value})
        self.data_dict.update(ld_value)

    def __delitem__(self, key):
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        del self.data_dict[full_iri]

    def __contains__(self, key):
        full_iri = self.ld_proc.expand_iri(self.active_ctx, key)
        return full_iri in self.data_dict

    def __eq__(self, other):
        if not isinstance(other, (dict, ld_dict)):
            return NotImplemented
        if ld_container.is_json_id(other):
            if "@id" in self:
                return self["@id"] == other["@id"]
            return self.data_dict == {}
        if ld_container.is_json_value(other):
            if {*self.keys()}.issubset({"@id", *other.keys()}):
                return ld_container.are_values_equal(self.data_dict, other)
            return False
        if isinstance(other, dict):
            other = self.from_dict(other, parent=self.parent, key=self.key, context=self.context)
        if "@id" in self and "@id" in other:
            return self["@id"] == other["@id"]
        keys_self = {*self.keys()}
        keys_other = {*other.keys()}
        unique_keys = keys_self.symmetric_difference(keys_other)
        if unique_keys and unique_keys != {"@id"}:
            return False
        for key in keys_self.intersection(keys_other):
            item = self[key]
            other_item = other[key]
            res = item.__eq__(other_item)
            if res == NotImplemented:
                res = other_item.__eq__(item)
            if res is False or res == NotImplemented:  # res is not True
                return False
        return True

    def __ne__(self, other):
        x = self.__eq__(other)
        if x is NotImplemented:
            return NotImplemented
        return not x

    def get(self, key, default=_NO_DEFAULT):
        try:
            value = self[key]
            return value
        except KeyError as e:
            if default is not ld_dict._NO_DEFAULT:
                return default
            raise e

    def update(self, other):
        for key, value in other.items():
            self[key] = value

    def keys(self):
        return self.data_dict.keys()

    def compact_keys(self):
        return map(
            lambda k: self.ld_proc.compact_iri(self.active_ctx, k),
            self.data_dict.keys()
        )

    def items(self):
        for k in self.data_dict.keys():
            yield k, self[k]

    @property
    def ref(self):
        return {"@id": self.data_dict['@id']}

    def to_python(self):
        res = {}
        for key in self.compact_keys():
            value = self[key]
            if isinstance(value, ld_container):
                value = value.to_python()
            res[key] = value
        return res

    @classmethod
    def from_dict(cls, value, *, parent=None, key=None, context=None, ld_type=None):
        ld_data = value.copy()

        ld_type = ld_container.merge_to_list(ld_type or [], ld_data.get('@type', []))
        if ld_type:
            ld_data["@type"] = ld_type

        data_context = ld_data.pop('@context', [])
        merged_contexts = ld_container.merge_to_list(data_context, context or [])
        full_context = []
        if parent is None and merged_contexts:
            ld_data["@context"] = merged_contexts
        elif parent is not None:
            full_context = parent.full_context + merged_contexts

        ld_value = cls.ld_proc.expand(ld_data, {"expandContext": full_context, "documentLoader": bundled_loader})
        ld_value = cls(ld_value, parent=parent, key=key, context=merged_contexts)

        return ld_value

    @classmethod
    def is_ld_dict(cls, ld_value):
        return cls.is_ld_node(ld_value) and cls.is_json_dict(ld_value[0])

    @classmethod
    def is_json_dict(cls, ld_value):
        if not isinstance(ld_value, dict):
            return False

        if any(k in ld_value for k in ["@set", "@graph", "@list", "@value"]):
            return False

        if ['@id'] == [*ld_value.keys()]:
            return False

        return True
