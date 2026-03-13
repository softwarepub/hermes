# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche
# SPDX-FileContributor: Stephan Druskat

from typing import Union
from typing_extensions import Self

from hermes.model.context_manager import HermesContext
from hermes.model.error import HermesContextError
from hermes.model.types import ld_dict
from hermes.model.types.ld_container import PYTHONIZED_LD_CONTAINER
from hermes.model.types.ld_context import ALL_CONTEXTS
from hermes.model.types.pyld_util import bundled_loader


class SoftwareMetadata(ld_dict):
    """
    An :class:`ld_dict` wrapper that has the standard context used by HERMES (:const:`ld_context.ALL_CONTEXTS`)
    and supports loading data from the HERMES cache.
    """

    def __init__(
        self: Self,
        data: Union[dict[str, PYTHONIZED_LD_CONTAINER], None] = None,
        extra_vocabs: Union[dict[str, str], None] = None
    ) -> None:
        """
        Create a new instance of an SoftwareMetadata.

        Args:
            data (dict[str, PYTHONIZED_LD_CONTAINER] | None): The data the SoftwareMetadata object starts out with.
            extra_vocabs (dict[str, str] | None): Extra JSON_LD context for the object.

        Returns:
            None:
        """
        ctx = ALL_CONTEXTS + [{**extra_vocabs}] if extra_vocabs is not None else ALL_CONTEXTS
        super().__init__([ld_dict.from_dict(data, context=ctx).data_dict if data else {}], context=ctx)

    @classmethod
    def load_from_cache(cls: type[Self], ctx: HermesContext, source: str) -> "SoftwareMetadata":
        """
        Loads the JSON_LD data from the given HermesContext object at the given source.\n
        Note that only data from "codemeta.json" or ("context.json" and "expanded.json") is loaded where "codemeta.json"
        is preferred.

        Args:
            ctx (HermesContext): The HERMES cache the data is loaded from.
            source (str): The directory the inside the cache the data is loaded from.

        Returns:
            SoftwareMetadata: The SoftwareMetadata loaded from the cache.

        Raises:
            HermesContextError: If neither of the listed files contains valid data for a SoftwareMetadata object.
        """
        # open the directory in the context
        with ctx[source] as cache:
            # Try loading from the "codemeta.json" file.
            try:
                return SoftwareMetadata(cache["codemeta"])
            except Exception:
                pass
            # Loading failed try from the other files.
            try:
                # Load and set the context.
                context = cache["context"]["@context"]
                data = SoftwareMetadata()
                data.active_ctx = data.ld_proc.initial_ctx(context, {"documentLoader": bundled_loader})
                data.context = context
                # Fill the SoftwareMetadata object with data.
                for key, value in cache["expanded"][0].items():
                    data[key] = value
                return data
            except Exception as e:
                # No data could be loaded, raise an error instead.
                raise HermesContextError("There is no (valid) data stored in the cache.") from e
