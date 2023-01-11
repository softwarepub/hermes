# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

import typing as t

from hermes.model import path as path_model


class HermesValidationError(Exception):
    """
    This exception should be thrown when input validation (e.g., during harvest) occurs.

    To be able to track and fix the error, you should use this in conjunction with the original exception if applicable:

    .. code:: python

        try:
             validate_some_data(src_file)
        except ValueError as e:
            raise HermesValidationError(src_file) from e
    """

    pass


class MergeError(Exception):
    """
    This exception should be raised when there is an error during a merge / set operation.
    """
    def __init__(self, path: path_model.ContextPath, old_Value: t.Any, new_value: t.Any, **kwargs):
        """
        Create a new merge incident.

        :param path: The path where the merge error occured.
        :param old_Value: Old value that was stored at `path`.
        :param new_value: New value that was to be assinged.
        :param kwargs: Tag data for the new value.
        """
        self.path = path
        self.old_value = old_Value
        self.new_value = new_value
        self.tag = kwargs
        super().__init__(f'Error merging {self.path} (ambiguous values "{self.old_value}" and "{self.new_value}")')
