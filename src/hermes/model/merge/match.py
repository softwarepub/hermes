# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from ..types import ld_dict

if TYPE_CHECKING:
    from .container import ld_merge_dict


def match_equals(a: Any, b: Any) -> bool:
    """
    Wrapper method for normal == comparison.

    :param a: First item for the comparison.
    :type a: Any
    :param b: Second item for the comparison.
    :type b: Any

    :return: Truth value of a == b.
    :rtype: bool
    """
    return a == b


def match_keys(
    *keys: list[str]
) -> Callable[[ld_merge_dict, ld_dict], bool]:
    """
    Creates a function taking to parameters that returns true
    if both given parameter have at least one common key in the given list of keys
    and for all common keys in the given list of keys the values of both objects are the same.

    :param keys: The list of important keys for the comparison method.
    :type keys: list[str]

    :return: A function comparing two given objects values for the keys in keys.
    :rtype: Callable[[ld_merge_dict, ld_dict], bool]
    """

    # create and return the match function using the given keys
    def match_func(left: ld_merge_dict, right: ld_dict) -> bool:
        """
        Compares left to right by checking if a) they have at least one common key in a predetermined list of keys and
        b) testing if both objects have equal values for all common keys in the predetermined key list.

        :param left: The first object for the comparison.
        :type left: ld_merge_dict
        :param right: The second object for the comparison.
        :type right: ld_dict

        :return: The result of the comparison.
        :rtype: bool
        """
        # TODO: This method maybe should try == comparison instead of returning false if active_keys == [].
        # create a list of all common important keys
        active_keys = [key for key in keys if key in left and key in right]
        # check if both objects have the same values for all active keys
        pairs = [(left[key] == right[key]) for key in active_keys]
        # return whether or not both objects had the same values for all active keys
        # and there was at least one active key
        return len(active_keys) > 0 and all(pairs)
    return match_func
