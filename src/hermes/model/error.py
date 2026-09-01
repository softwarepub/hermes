# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Stephan Druskat <stephan.druskat@dlr.de>

from typing import Any, Union


class HermesValidationError(Exception):
    """
    This exception should be raised when an error occurs during input validation (e.g., during harvest).

    To be able to track and fix the error, you should use this in conjunction with the original exception if applicable:

    .. code:: python

        try:
             validate_some_data(src_file)
        except ValueError as e:
            raise HermesValidationError(src_file) from e
    """
    pass


class HermesCacheError(Exception):
    """
    This exception should be raised when interacting with the model context.
    # TODO Change class name and docstring if we decide to call it differently
    # TODO in https://github.com/softwarepub/hermes/issues/392.

    To be able to track and fix the error, you should use this in conjunction with the original exception if applicable:

    .. code:: python

        try:
             context[term]
        except ValueError as e:
            raise HermesCacheError(term) from e
    """
    pass


class HermesMergeError(Exception):
    """
    This exception should be raised when there is an error during a merge / set operation.

    Attributes:
        path (list[str | int]): The path where the merge error occurred.
        old_value (Any): Old value that was stored at `path`.
        new_value (Any): New value that was to be assigned .
        tag: Tag data for the new value.
    """
    def __init__(self, path: list[Union[str, int]], old_value: Any, new_value: Any, **kwargs) -> None:
        """
        Create a new merge incident.

        Args:
            path (list[str | int]): The path where the merge error occurred.
            old_value (Any): Old value that was stored at `path`.
            new_value (Any): New value that was to be assigned .
            kwargs: Tag data for the new value.

        Returns:
            None:
        """
        self.path = path
        self.old_value = old_value
        self.new_value = new_value
        self.tag = kwargs
        super().__init__(f'Error merging {self.path} (ambiguous values "{self.old_value}" and "{self.new_value}")')
