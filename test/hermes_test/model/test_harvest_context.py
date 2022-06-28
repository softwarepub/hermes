from importlib.metadata import EntryPoint

from hermes.model.context import HermesContext, HermesHarvestContext


class test_context_default():
    ctx = HermesContext()
    hctx = HermesHarvestContext(ctx, EntryPoint('foo', 'spam', 'eggs'))
