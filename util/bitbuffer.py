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

import math
from collections import deque
from collections.abc import Iterable


class BitBuffer:
    """
    A utility class that makes handling bits (and not bytes) easy.
    """
    # The maximum number of bits each integer in the saved_data deque will have:
    BITS_PER_INT: int = 32

    # A mask used to extract only the first 'BITS_PER_INT' bits in a number:
    FULL_INT_MASK: int = (1 << BITS_PER_INT) - 1

    __slots__ = [
        # Since the buffer is designed to hold lots of bits, we'll hold them as a deque of integers (a deque allows us
        # to store data non-consecutively, and the integer type allows easy bit manipulation):
        '__saved_data',

        # The current int we are writing to (it is still not in the `saved_data` attribute):
        '__current_int',

        # The index of the bit in 'current_int' that will be written to in the next method call. Notice that it
        # points to the bit that you get if you call `(current_int >> (BITS_PER_INT - 1 - bit_idx)) & 1`. This is done
        # in order to preserve the order of bit insertions:
        '__bit_idx'
    ]

    def __init__(self) -> 'BitBuffer':
        """
        Creates an empty Bitbuffer.
        """
        # Initialize everything:
        self.__saved_data: deque[int] = deque()
        self.__current_int: int = 0
        self.__bit_idx = 0

    def insert_bits(self, bits_container: int, bits_num: int) -> 'BitBuffer':
        """
        Inserts a variable amount of bits into the buffer.
        :param bits_container: An integer containing the bits that will be inserted into the buffer. Pay attention that
                               the bits that will be inserted are the least significant bits, from the most significant
                               of them to the least.
                               For example:
                               >>> buffer = BitBuffer()
                               >>> buffer.insert_bits(bits_container=0b101010, bits_num=5)
                               >>> # Buffer now contains the bits "01010", in that order (left to right)
        :param bits_num: The number of bits to extract from the integer. If this number is larger than needed to
                         represent the number saved in `bits_container`, zeroes will be appended to the start of the
                         number (because adding zeroes to the start doesn't change the value of the number).
        :return: The current BitBuffer object, in order to support the builder pattern.
        """
        # Extract the necessary bits only:
        bits_container &= (1 << bits_num) - 1

        # Insert as many bits as possible into the current integer:
        free_bits = BitBuffer.BITS_PER_INT - self.__bit_idx
        if free_bits > bits_num:
            self.__current_int |= (bits_container << (free_bits - bits_num)) & BitBuffer.FULL_INT_MASK
            self.__bit_idx += bits_num
        else:
            # Insert what you can into the current integer:
            next_int_bits_count = bits_num - free_bits
            self.__current_int |= bits_container >> next_int_bits_count
            self.__save_current_int()

            # Call the method again with the remaining bits:
            self.insert_bits(bits_container, next_int_bits_count)

        return self

    def __save_current_int(self) -> None:
        """
        Saves the current integer in the deque. Only use if the integer is full.
        """
        self.__saved_data.append(self.__current_int)
        self.__current_int = 0
        self.__bit_idx = 0

    def __len__(self) -> int:
        """
        Calculates and returns the number of bits held in the buffer.
        :return: The number of bits held in the buffer.
        """
        return BitBuffer.BITS_PER_INT * len(self.__saved_data) + self.__bit_idx
    
    def __getitem__(self, bit_offset: int) -> int:
        """
        Given an offset of a bit from the start of the buffer, the method returns the bit's value (1 or 0).
        :param bit_offset: The offset of the specified bit from the start of the buffer. Must be less than the buffer's
                           length.
        :return: The value of the bit at offset `bit_offset`.
        """
        # Pre-compute length:
        buffer_len = len(self)
        
        # If it's a negative offset, convert it to a positive one after making sure it isn't out of bounds:
        if bit_offset < 0:
            if abs(bit_offset) > buffer_len:
                raise IndexError(f"Negative index {bit_offset} out of bounds (buffer length is {buffer_len})")
            return self[buffer_len + bit_offset]
        
        # Check for offset issues:
        if bit_offset >= buffer_len:
            raise IndexError(f"Bit offset out of bounds (offset={bit_offset}, length={buffer_len}")
        
        # Check if it's inside one of the blocks in the deque:
        block_idx = bit_offset // BitBuffer.BITS_PER_INT
        in_deque = block_idx < len(self.__saved_data)
        
        # Get the bit's container:
        container: int = self.__saved_data[block_idx] if in_deque else self.__current_int
        container_idx = bit_offset % BitBuffer.BITS_PER_INT
        
        # Get the bit:
        return (container >> (BitBuffer.BITS_PER_INT - (container_idx + 1))) & 1

    def __bytes__(self):
        """
        Extracts the bits saved in the buffer as a bytes object. The order in which the bits were inserted into the
        object is preserved.
        :return: A bytes object containing the bits in the object.
        """
        # Calculate the amount of bytes needed beforehand:
        saved_ints_bytes_count = math.ceil(BitBuffer.BITS_PER_INT / 8) * len(self.__saved_data)
        current_int_bytes_count = math.ceil(self.__bit_idx / 8)
        bytes_needed = saved_ints_bytes_count + current_int_bytes_count

        # Create a bytearray with this size:
        stored_bits = bytearray(bytes_needed)

        # Insert the saved integers first (their bits are already ordered according to user insertions):
        for int_idx, saved_int in enumerate(self.__saved_data):
            # An integer has 4 bytes:
            for i in range(4):
                stored_bits[int_idx * 4 + i] = BitBuffer.__get_byte_from_int(saved_int, i)

        # Add the current int as well:
        for i in range(current_int_bytes_count):
            stored_bits[saved_ints_bytes_count + i] = BitBuffer.__get_byte_from_int(self.__current_int, i)

        return bytes(stored_bits)

    def __repr__(self) -> str:
        return (
                "".join(bin(num)[2:].zfill(BitBuffer.BITS_PER_INT) for num in self.__saved_data) +  # saved_data
                bin(self.__current_int)[2:].zfill(BitBuffer.BITS_PER_INT)[:self.__bit_idx]  # current int
        )
    
    def __eq__(self, other: 'BitBuffer'):
        if other is None:
            return False
        elif self is other:
            return True
        elif not isinstance(other, BitBuffer):
            return False
        else:
            return (self.__bit_idx == other.__bit_idx and self.__current_int == other.__current_int and
                    self.__saved_data == other.__saved_data)

    @staticmethod
    def __get_byte_from_int(integer: int, byte_idx: int) -> int:
        """
        An integer is made of four bytes. This method returns a single byte out of those four, based on its index.
        :param integer: The integer that the resulting byte will be extracted from.
        :param byte_idx: The index of the byte inside the integer. This value must be in the range [0, 4), where index 0
                         is referring to the most significant byte of the integer (i.e: the Xs part:
                         XXXXXXXX -------- -------- --------).
        :return: The byte at the specified index inside the integer.
        :raises ValueError: If byte_idx is not in the range [0, 4).
        """
        if byte_idx < 0 or byte_idx > 3:
            raise ValueError(f"Byte index must be in the range [0, 4) (got {byte_idx})")

        return integer >> (8 * (3 - byte_idx)) & 0xFF

    @staticmethod
    def concatenate(buffers: Iterable['BitBuffer']) -> 'BitBuffer':
        """
        Given an iterable of BitBuffer objects, the function concatenates the bits saved in them and returns them in a
        single BitBuffer object.
        The order of the bits is preserved, according to the order of the buffers in the given iterable.
        This function does NOT mutate the given buffers.
        :param buffers: An iterable of buffers whose contents will be concatenated.
        :return: A BitBuffer object containing all bits saved in the given buffers.
        """
        # Initialize output buffer:
        output = BitBuffer()

        for buffer in buffers:
            # Insert every saved integer:
            for saved_int in buffer.__saved_data:
                output.insert_bits(saved_int, BitBuffer.BITS_PER_INT)
            # Insert the current integer (if it's not loaded, the buffer's bit_idx will be 0, and nothing will be
            # inserted):
            unused_bits = BitBuffer.BITS_PER_INT - buffer.__bit_idx
            output.insert_bits(buffer.__current_int >> unused_bits, buffer.__bit_idx)

        return output
    
    @staticmethod
    def from_bytes(data: bytes) -> 'BitBuffer':
        """
        Creates a new BitBuffer with the given data already loaded inside of it.
        Pay attention that all bits inside every byte are saved in the buffer, even if the byte starts with 0 bits.
        :param data: Some data which will be 'wrapped' by a new BitBuffer.
        :return: A new BitBuffer object containing the given data.
        """
        # Empty case:
        if len(data) == 0:
            return BitBuffer()
        
        buffer = BitBuffer()
        current_int = 0
        bits_count = 0
        
        # Set blocks in the deque:
        for byte in data:
            current_int = (current_int << 8) | byte
            bits_count += 8
            
            if bits_count >= BitBuffer.BITS_PER_INT:
                buffer.__saved_data.append(current_int)
                bits_count = current_int = 0
        
        # Load the current int and bit_idx (align current_int's bits to start at the most significant bit):
        buffer.__current_int = current_int << (BitBuffer.BITS_PER_INT - bits_count)
        buffer.__bit_idx = bits_count
        
        return buffer
    