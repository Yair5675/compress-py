class TooManyEncodingsException(Exception):
    """
    A custom exception that is raised when the dictionary used in the LZW algorithm exceeds its maximum size.
    """
    def __init__(self, message="The dictionary reached its maximum size"):
        self.message = message
        super().__init__(message)
