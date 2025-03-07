#     Compress-py  A command-line interface for compressing files
#     Copyright (C) 2025  Yair Ziv
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from enum import Enum


class TooManyEncodingsException(Exception):
    """
    A custom exception that is raised when the dictionary used in the LZW algorithm exceeds its maximum size.
    """
    def __init__(self, message="The dictionary reached its maximum size"):
        self.message = message
        super().__init__(message)


class OutOfMemoryStrategy(str, Enum):
    """
    During the LZW algorithm, the dictionary's size may not be sufficient. In this case, the program needs to know how
    to proceed.
    This enum contains different strategies to handle this case.
    """
    # The simplest strategy - if it ever happens, abort the execution:
    ABORT = "ABORT"

    # If we run out of memory, stop storing new entries. This hurts compression efficiency:
    STOP_STORE = "STOP_STORE"

    # Add just enough memory to complete the algorithm. In practice - this means incrementing the maximum size by one
    # whenever we exceed it:
    USE_MINIMUM_REQUIRED = "USE_MINIMUM_REQUIRED"
