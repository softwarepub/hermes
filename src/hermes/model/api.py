from hermes.model.types import ld_dict

from hermes.model.types.ld_context import ALL_CONTEXTS

class SoftwareMetadata(ld_dict):

    def __init__(self, data: dict=None, extra_vocabs: dict[str, str]=None) -> None:
        ctx = ALL_CONTEXTS + [{**extra_vocabs}] if extra_vocabs is not None else ALL_CONTEXTS
        super().__init__([data or {}], context=ctx)

