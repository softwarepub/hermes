# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from typing import Any, Callable

from ..types import ld_dict


def match_keys(*keys: list[str], fall_back_to_equals: bool = False) -> Callable[[Any, Any], bool]:
    """
    Creates a function taking to parameters that returns true
    if both given parameter have at least one common key in the given list of keys
    and for all common keys in the given list of keys the values of both objects are the same.<br>
    If fall_back_to_equals is True, the returned function returns the value of normal == comparison
    if no key from keys is in both objects.

    :param keys: The list of important keys for the comparison method.
    :type keys: list[str]
    :param fall_back_to_equals: Whether or not a fall back option should be used.
    :type fall_back_to_equals: bool

    :return: A function comparing two given objects values for the keys in keys.
    :rtype: Callable[[ld_merge_dict, ld_dict], bool]
    """

    # create and return the match function using the given keys
    def match_func(left: Any, right: Any) -> bool:
        """
        Compares left to right by checking if a) they have at least one common key in a predetermined list of keys and
        b) testing if both objects have equal values for all common keys in the predetermined key list.<br>
        It may fall back on == if no common key in the predetermined list of keys exists.

        :param left: The first object for the comparison.
        :type left: ld_merge_dict
        :param right: The second object for the comparison.
        :type right: ld_dict

        :return: The result of the comparison.
        :rtype: bool
        """
        if not (isinstance(left, ld_dict) and isinstance(right, ld_dict)):
            return fall_back_to_equals and (left == right)
        # create a list of all common important keys
        active_keys = [key for key in keys if key in left and key in right]
        # fall back to == if no active keys
        if fall_back_to_equals and not active_keys:
            return left == right
        # check if both objects have the same values for all active keys
        pairs = [(left[key] == right[key]) for key in active_keys]
        # return whether or not both objects had the same values for all active keys
        # and there was at least one active key
        return len(active_keys) > 0 and all(pairs)
    return match_func


def match_person(left: Any, right: Any) -> bool:
    if not (isinstance(left, ld_dict) and isinstance(right, ld_dict)):
        return left == right
    if "@id" in left and "@id" in right:
        return left["@id"] == right["@id"]
    if "schema:email" in left and "schema:email" in right:
        mails_right = right["schema:email"]
        return any((mail in mails_right) for mail in left["schema:email"])
    return left == right


def match_multiple_types(
    *functions_for_types: list[tuple[str, Callable[[Any, Any], bool]]],
    fall_back_function: Callable[[Any, Any], bool] = match_keys("@id", fall_back_to_equals=True)
) -> Callable[[Any, Any], bool]:
    def match_func(left: Any, right: Any) -> bool:
        if not ((isinstance(left, ld_dict) and isinstance(right, ld_dict)) and "@type" in left and "@type" in right):
            return fall_back_function(left, right)
        types_left = left["@type"]
        types_right = right["@type"]
        for ld_type, func in functions_for_types:
            if ld_type in types_left and ld_type in types_right:
                return func(left, right)
        return fall_back_function(left, right)
    return match_func
