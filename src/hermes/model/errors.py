# SPDX-FileCopyrightText: 2022 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel

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
