from hermes.model.types import ld_dict, ld_list

from hermes.model.types.ld_context import ALL_CONTEXTS


class SoftwareMetadata(ld_dict):

    def __init__(self, data: dict = None, extra_vocabs: dict[str, str] = None) -> None:
        ctx = ALL_CONTEXTS + [{**extra_vocabs}] if extra_vocabs is not None else ALL_CONTEXTS
        super().__init__([ld_dict.from_dict(data, context=ctx).data_dict if data else {}], context=ctx)

    def add(self, key, value):
        if key not in self:
            self[key] = value
            return
        if isinstance(val := self[key], ld_list):
            val.append(value)
        else:
            temp = ld_list([{"@list": []}], parent=self, key=self.ld_proc.expand_iri(self.active_ctx, key),
                           context=self.context)
            temp.extend([val, value])
            self[key] = temp
