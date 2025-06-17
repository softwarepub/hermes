from hermes.model.types import ld_dict, ld_list, ld_context

from .strategy import REPLACE_STRATEGY, CODEMETA_STRATEGY, PROV_STRATEGY
from ..types.pyld_util import bundled_loader


class _ld_merge_container:
    def _to_python(self, full_iri, ld_value):
        value = super()._to_python(full_iri, ld_value)
        if isinstance(value, ld_dict) and not isinstance(value, ld_merge_dict):
            value = ld_merge_dict(
                value.ld_value,
                self.prov_doc,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context
            )
        if isinstance(value, ld_list) and not isinstance(value, ld_merge_list):
            value = ld_merge_list(
                value.ld_value,
                self.prov_doc,
                parent=value.parent,
                key=value.key,
                index=value.index,
                context=value.context
            )
        return value


class ld_merge_list(_ld_merge_container, ld_list):
    def __init__(self, data, prov_doc, *, parent=None, key=None, index=None, context=None):
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        self.prov_doc = prov_doc


class ld_merge_dict(_ld_merge_container, ld_dict):
    def __init__(self, data, prov_doc, *, parent=None, key=None, index=None, context=None):
        super().__init__(data, parent=parent, key=key, index=index, context=context)

        self.update_context(ld_context.HERMES_PROV_CONTEXT)

        self.prov_doc = prov_doc
        self.strategies = {**REPLACE_STRATEGY}
        self.add_strategy(CODEMETA_STRATEGY)
        self.add_strategy(PROV_STRATEGY)

    def update_context(self, other_context):
        if other_context:
            if len(self.context) < 1 or not isinstance(self.context[-1], dict):
                self.context.append({})

            if not isinstance(other_context, list):
                other_context = [other_context]
            for ctx in other_context:
                if isinstance(ctx, dict):
                    self.context[-1].update(ctx)
                elif ctx not in self.context:
                    self.context.insert(0, ctx)

            self.active_ctx = self.ld_proc.inital_ctx(self.context, {"documentLoader": bundled_loader})

    def update(self, other):
        if isinstance(other, ld_dict):
            self.update_context(other.context)

        super().update(other)

    def add_strategy(self, strategy):
        for key, value in strategy.items():
            self.strategies[key] = {**value, **self.strategies.get(key, {})}

    def __setitem__(self, key, value):
        if key in self:
            value = self._merge_item(key, value)
        super().__setitem__(key, value)

    def match(self, key, value, match):
        for index, item in enumerate(self[key]):
            if match(item, value):
                if isinstance(item, ld_dict) and not isinstance(item, ld_merge_dict):
                    item = ld_merge_dict(item.ld_value, self.prov_doc,
                                         parent=item.parent, key=item.key, index=index, context=item.context)
                elif isinstance(item, ld_list) and not isinstance(item, ld_merge_list):
                    item = ld_merge_list(item.ld_value, self.prov_doc,
                                         parent=item.parent, key=item.key, index=index, context=item.context)
                return item

    def _merge_item(self, key, value):
        strategy = {**self.strategies[None]}
        ld_types = self.data_dict.get('@type', [])
        for ld_type in ld_types:
            strategy.update(self.strategies.get(ld_type, {}))

        merger = strategy.get(key, strategy[None])
        return merger.merge(self, [*self.path, key], self[key], value)

    def _add_related(self, rel, key, value):
        with self.prov_doc.make_node('Entity', {
            "@type": "schema:PropertyValue",
            "schema:name": str(key),
            "schema:value": str(value),
        }) as entity_node:
            if rel not in self:
                rel_iri = self.ld_proc.expand_iri(self.active_ctx, rel)
                self[rel] = ld_list.from_list([entity_node.ref], container="@set", parent=self, key=rel_iri)
            else:
                self[rel].append(entity_node.ref)

    def reject(self, key, value):
        self._add_related("hermes-rt:reject", key, value)

    def replace(self, key, value):
        self._add_related("hermes-rt:replace", key, value)
