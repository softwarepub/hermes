from hermes.model.context_manager import HermesContext, HermesContexError
from hermes.model.types import ld_dict
from hermes.model.types.ld_context import ALL_CONTEXTS
from hermes.model.types.ld_dict import bundled_loader


class SoftwareMetadata(ld_dict):

    def __init__(self, data: dict = None, extra_vocabs: dict[str, str] = None) -> None:
        ctx = ALL_CONTEXTS + [{**extra_vocabs}] if extra_vocabs is not None else ALL_CONTEXTS
        super().__init__([ld_dict.from_dict(data, context=ctx).data_dict if data else {}], context=ctx)

    @classmethod
    def load_from_cache(cls, ctx: HermesContext, source: str) -> "SoftwareMetadata":
        with ctx[source] as cache:
            try:
                return SoftwareMetadata(cache["codemeta"])
            except Exception:
                pass
            try:
                context = cache["context"]["@context"]
                data = SoftwareMetadata()
                data.active_ctx = data.ld_proc.initial_ctx(context, {"documentLoader": bundled_loader})
                data.context = context
                for key, value in cache["expanded"][0]:
                    data[key] = value
                return data
            except Exception as e:
                raise HermesContexError("There is no (valid) data stored in the cache.") from e
