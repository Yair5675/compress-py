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

from abc import ABC, abstractmethod


class Compressor(ABC):
    """
    An abstract class representing the basic requirements for a compressor.
    """

    @abstractmethod
    def encode(self, input_data: bytes) -> bytes:
        """
        Encodes the input data according to a certain compression algorithm.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed.
        """
        pass

    @abstractmethod
    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the compressed data according to a certain decompression algorithm. It should be noted
        that the decompression algorithm assumes the data was compressed in a certain way, and if not
        the method will fail.
        :param compressed_data: A data that was compressed according to a certain algorithm matching the
                                current decompression algorithm.
        :return: The decompressed data.
        """
        pass
