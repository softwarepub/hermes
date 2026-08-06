# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche


from typing import Union
from typing_extensions import Self

from hermes.commands.base import HermesCommand
from hermes.model.merge.action import MergeAction
from hermes.model.merge.container import ld_merge_dict, ld_merge_list
from hermes.model.types import ld_dict, ld_list
from hermes.model.types.ld_container import BASIC_TYPE, TIME_TYPE
from hermes.model.types.ld_context import iri_map as iri
from .base import HermesProcessPlugin


class InvenioMerge(MergeAction):
    """ :class:`MergeAction` providing a merge function that tries to conform with Invenios metadata restrictions. """
    def merge(
        self: Self,
        target: ld_merge_dict,
        key: list[Union[str, int]],
        value: Union[ld_merge_list, str],
        update: Union[BASIC_TYPE, TIME_TYPE, ld_dict, ld_list]
    ) -> ld_merge_list:
        print(key, value, update)
        types = target.get("@type", [])
        print(types)
        if key[-1] == iri["schema:license"] and (iri["schema:SoftwareSourceCode"] in types or iri["schema:SoftwareApplication"] in types):
            if len(value) == 1:
                if isinstance(value[0], str) or (
                    isinstance(value[0], (dict, ld_merge_dict)) and [*value[0].keys()] == ["@id"]
                ):
                    if value != update:
                        target.reject(key, update)
                    return value
            if isinstance(update, ld_list) and len(update) == 1:
                if isinstance(update[0], str) or (
                    isinstance(update[0], (dict, ld_merge_dict)) and [*update[0].keys()] == ["@id"]
                ):
                    target.replace(key, value)
                    return update
            target.reject(key, update)
            return value
        if ((key[-1] == iri["schema:familyName"] and iri["schema:Person"] in types) or
            (key[-1] == iri["schema:name"] and iri["schema:Person"] in types) or
            (key[-1] == iri["schema:name"] and (iri["schema:SoftwareSourceCode"] in types or iri["schema:SoftwareApplication"] in types))
        ):
            if len(value) == 1:
                if value != update:
                    target.reject(key, update)
                return value
            if len(update) == 1:
                target.replace(key, value)
                return update
            if len(value) == len(update) == 0:
                return value
            target.reject(key, update)
            return value
        if ((key[-1] == iri["schema:version"] or key[-1] == iri["schema:description"]) and
            (iri["schema:SoftwareSourceCode"] in types or iri["schema:SoftwareApplication"] in types)
        ):
            if len(value) == 1:
                if value != update:
                    target.reject(key, update)
                return value
            if len(update) == 1:
                target.replace(key, value)
                return update
            if len(value) == 0 or len(update) == 0:
                return []
            target.reject(key, update)
            return value
        print("fail")


class InvenioProcessPlugin(HermesProcessPlugin):
    def __call__(self, command: HermesCommand) -> dict[Union[str, None], dict[Union[str, None], MergeAction]]:
        merger = InvenioMerge()
        return {
            iri["schema:SoftwareSourceCode"]: {
                iri["schema:"+term]: merger for term in ["version", "name", "description", "license"]
            },
            iri["schema:SoftwareApplication"]: {
                iri["schema:"+term]: merger for term in ["version", "name", "description", "license"]
            },
            iri["schema:Person"]: {
                iri["schema:"+term]: merger for term in ["familyName", "name"]
            }
        }
