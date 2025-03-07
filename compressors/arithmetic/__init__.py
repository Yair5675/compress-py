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

from compressors import Compressor
from compressors.arithmetic.interval_state import IntervalState
from compressors.arithmetic.bits_system import BitsSystem, InsufficientValueRange


class ArithmeticCompressor(Compressor):
    __slots__ = (
        # The bits system used in encoding/decoding:
        'bits_system',
    )

    def __init__(self, system: BitsSystem) -> 'ArithmeticCompressor':
        self.bits_system = system

    def encode(self, input_data: bytes) -> bytes:
        # TODO: Compress using the Encoder class
        pass

    def decode(self, compressed_data: bytes) -> bytes:
        # TODO: Decompress using the Decoder class
        pass
