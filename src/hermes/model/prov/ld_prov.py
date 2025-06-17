import uuid

from hermes.model.prov.ld_prov_node import ld_prov_node
from hermes.model.types.pyld_util import bundled_loader

from hermes.model.types import ld_list, ld_context, iri_map as iri


class ld_record_call:
    def __init__(self, callable):
        self.callable = callable
        self.instance = None

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self, *args, **kwargs):
        if self.instance:
            pre = [self.instance]
        else:
            pre = []

        with self.prov_doc[-1].make_node('prov:Activity') as activity:
            for arg in (*args, *kwargs.values()):
                activity.add_entity('prov:used', arg)

            with activity.timer:
                res = self.callable(*pre, *args, **kwargs)

            activity.add_entity('prov:generated', res)
            activity.commit()

        return res

    @classmethod
    def patch(cls, target, *funcs):
        for name in funcs:
            callable = getattr(target, name)
            setattr(target, name, cls(callable))


class ld_prov(ld_list):
    ld_base_ctx = ld_context.HERMES_PROV_CONTEXT

    NODE_IRI_FORMAT = "graph://{uuid}/{type}#{index}"
    PROV_DOC_IRI = ld_context.iri_map['hermes-rt', "graph"]

    def __init__(self, data=None, *, parent=None, key=None, context=None):
        self.uuid = uuid.uuid1()
        self.counter = {}

        if data is None:
            data = [{"@graph": []}]
            key = key or self.PROV_DOC_IRI
            context = context or ld_context.HERMES_PROV_CONTEXT

        super().__init__(data, parent=parent, key=key or self.PROV_DOC_IRI, context=context)

    def attach(self, ld_data):
        if self.parent is None:
            pending_nodes = self[:]
            self.item_list.clear()

            self.parent = ld_data
            self.active_ctx = self.ld_proc.process_context(self.parent.active_ctx, self.full_context,
                                                           {"documentLoader": bundled_loader})
            ld_data.add_context(self.ld_base_ctx)
            ld_data[self.key] = self

            for node in pending_nodes:
                self.append(node)

    def make_node_id(self, prov_type):
        prov_type = self.ld_proc.compact_iri(self.active_ctx, prov_type)
        next_index = self.counter.get(prov_type, 1)
        self.counter[prov_type] = next_index + 1
        return self.NODE_IRI_FORMAT.format(uuid=self.uuid, type=prov_type, index=next_index)

    def make_node(self, prov_type, data=None):
        return ld_prov_node.from_dict(data, parent=self, ld_type=iri['prov', prov_type])

    def get(self, **query):
        for node in self.item_list:
            if all(node.get(k, None) == v for k, v in query.items()):
                yield node

    def compact(self, context=None):
        return super().compact(context or self.ld_base_ctx)

    def push(self, activity_data=None):
        prov_doc = _ld_prov_child(self, context=self.context)
        push_activity = prov_doc.make_node('Activity', activity_data)
        return prov_doc, push_activity


class _ld_prov_child(ld_prov):
    def __init__(self, parent_prov, data=None, *, parent=None, key=None, context=None):
        super().__init__(data, parent=parent, key=key, context=context)

        self.parent_prov = parent_prov

    def finish(self):
        self.parent_prov.item_list.extend(self.item_list)
