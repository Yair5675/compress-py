from enum import Enum, auto


class TooManyEncodingsException(Exception):
    """
    A custom exception that is raised when the dictionary used in the LZW algorithm exceeds its maximum size.
    """
    def __init__(self, message="The dictionary reached its maximum size"):
        self.message = message
        super().__init__(message)


class OutOfMemoryStrategy(Enum):
    """
    During the LZW algorithm, the dictionary's size may not be sufficient. In this case, the program needs to know how
    to proceed.
    This enum contains different strategies to handle this case.
    """
    # The simplest strategy - if it ever happens, abort the execution:
    ABORT = auto()

    # If we run out of memory, stop storing new entries. This hurts compression efficiency:
    STOP_STORE = auto()

    # Add just enough memory to complete the algorithm. In practice - this means incrementing the maximum size by one
    # whenever we exceed it:
    USE_MINIMUM_REQUIRED = auto()
