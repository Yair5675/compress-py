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

from dataclasses import dataclass
from util.bitbuffer import BitBuffer


@dataclass
class HuffmanEncoding:
    # The length of the encoding in bits (necessary in case the encoding starts with 0):
    bit_length: int
    # The actual encoding:
    encoding: int

    def load_to_buffer(self, bit_buffer: BitBuffer) -> None:
        """
        Inserts the bits of the huffman encoding into the bit buffer.
        :param bit_buffer: A bit buffer that the huffman encoding's bits will be inserted to.
        """
        bit_buffer.insert_bits(self.encoding, max(1, self.bit_length))

    def __repr__(self) -> str:
        return str(bin(self.encoding)[2:]).zfill(self.bit_length)

    def __hash__(self):
        return (self.encoding << 10) | self.bit_length
