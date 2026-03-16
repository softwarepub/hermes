# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from typing import Any, Callable

from hermes.model.types import ld_dict


def match_keys(*keys: list[str], fall_back_to_equals: bool = False) -> Callable[[Any, Any], bool]:
    """
    Creates a function taking to parameters that returns true
    if both given parameter have at least one common key in the given list of keys
    and for all common keys in the given list of keys the values of both objects are the same.\n
    If fall_back_to_equals is True, the returned function returns the value of normal == comparison
    if no key from keys is in both objects.

    Args:
        keys (list[str]): The list of important keys for the comparison method.
        fall_back_to_equals (bool): Whether or not a fall back option should be used.

    Returns:
        Callable[[Any, Any], bool]: A function comparing two given objects values for the keys in keys.
    """

    # create and return the match function using the given keys
    def match_func(left: Any, right: Any) -> bool:
        """
        Compares left to right by checking if

        - they have at least one common key in a predetermined list of keys and
        - testing if both objects have equal values for all common keys in the predetermined key list.

        It may fall back on == if no common key in the predetermined list of keys exists.

        Args:
            left (Any): The first object for the comparison.
            right (Any): The second object for the comparison.

        Returns:
            bool: The result of the comparison.
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
    """
    Compares two objects assuming they are representing schema:Person's
    if they are not ld_dicts, == is used as a fallback.\n
    If both objects have an @id value, the truth value returned by this function is the comparison of both ids.\n
    If either other has no @id value and both objects have at least one email value,
    they are considered equal if they have one common email.\n
    If the equality of the objects is not yet decided, == comparison of the objects is returned.

    Args:
        left (Any): The first object for the comparison.
        right (Any): The second object for the comparison.

    Returns:
        bool: The result of the comparison.
    """
    if not (isinstance(left, ld_dict) and isinstance(right, ld_dict)):
        return left == right
    if "@id" in left and "@id" in right:
        return left["@id"] == right["@id"]
    if "schema:email" in left and "schema:email" in right:
        if len(left["schema:email"]) > 0 and len(right["schema:email"]) > 0:
            mails_right = right["schema:email"]
            return any((mail in mails_right) for mail in left["schema:email"])
    return left == right


def match_multiple_types(
    *functions_for_types: list[tuple[str, Callable[[Any, Any], bool]]],
    fall_back_function: Callable[[Any, Any], bool] = match_keys("@id", fall_back_to_equals=True)
) -> Callable[[Any, Any], bool]:
    """
    Returns a function that compares two objects using the given functions.

    Args:
        functions_for_types (list[tuple[str, Callable[[Any, Any], bool]]]): Tuples of type and match_function.
            The returned function will compare two objects of a the same, given type with the specified function.
        fall_back_function (Callable[[Any, Any], bool]): The fallback for comparison if the objects that are being
            compared don't have a common type with specified compare function or at least one object
            is not a JSON-LD dictionary.

    Returns:
        Callable[[Any, Any], bool]: The function that compares the two given objects using the given functions.
    """

    # create and return the match function using the given keys
    def match_func(left: Any, right: Any) -> bool:
        """
        Compares two objects using a predetermined function if either objects is not an ld_dict
        or they don't have a common type in a predetermined list of types.\n
        If the objects are ld_dicts and have the same type with a known comparison function this is used instead.

        Args:
            left (Any): The first object for the comparison.
            right (Any): The second object for the comparison.

        :return: The result of the comparison.
        :rtype: bool
        """
        # If at least one of the objects is not an ld_dict or contains no value for the key "@type", use the fallback.
        if not (isinstance(left, ld_dict) and isinstance(right, ld_dict) and "@type" in left and "@type" in right):
            return fall_back_function(left, right)
        # Extract the list of types
        types_left = left["@type"]
        types_right = right["@type"]
        # Iterate over all known type, match_function pairs.
        # If one type is in both objects return the result of the comparison with the match_function.
        for ld_type, func in functions_for_types:
            if ld_type in types_left and ld_type in types_right:
                return func(left, right)
        # No common type with known match_function: Fallback
        return fall_back_function(left, right)
    return match_func
