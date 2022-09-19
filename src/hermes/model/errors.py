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
    def __init__(self, path, old_Value, new_value, **kwargs):
        self.path = path
        self.old_value = old_Value
        self.new_value = new_value
        self.tag = kwargs
        super().__init__(f'Error merging {self.path} (ambiguous values "{self.old_value}" and "{self.new_value}")')
