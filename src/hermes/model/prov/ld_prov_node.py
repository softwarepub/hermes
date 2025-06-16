from datetime import datetime

from hermes.model.types import ld_container, ld_dict, ld_list, ld_context
from hermes.model.types.ld_context import iri_map as iri


class ld_prov_node(ld_dict):
    class Timer:
        def __init__(self, data): self.data = data
        def now(self): return datetime.now()
        def __enter__(self): self.data["prov:startedAtTime"] = self.now()
        def __exit__(self, *args): self.data["prov:endedAtTime"] = self.now()

    @property
    def timer(self):
        return ld_prov_node.Timer(self)

    def __init__(self, data, *, parent=None, key=None, context=None):
        self.ld_iri = None
        self.finished = False

        super().__init__(data, parent=parent, key=key, context=context)

    def __enter__(self):
        if self.finished:
            raise ValueError("Already committed")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            raise exc_type(exc_val)

    @property
    def ref(self):
        if self.ld_iri is None:
            for prov_type in self.data_dict.get("@type", []):
                if prov_type.startswith(ld_context.PROV_PREFIX):
                    break
            else:
                prov_type = "Node"

            self.ld_iri = self.parent.make_node_id(prov_type)

        return {"@id": self.ld_iri}

    def add_related(self, rel, prov_type, value):
        if self.finished:
            raise ValueError("Already committed")

        rel_iri = self.ld_proc.expand_iri(self.active_ctx, rel)
        with self.parent.make_node(prov_type, value) as entity_node:
            if not rel in self:
                self[rel] = ld_list.from_list([entity_node.ref], container="@set", parent=self, key=rel_iri)
            else:
                self[rel].append(entity_node.ref)

        return entity_node

    def commit(self):
        if not self.finished:
            self.finished = True
            self["@id"] = self.ref["@id"]
            self.parent.append(self)
