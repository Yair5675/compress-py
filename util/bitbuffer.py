from typing import Optional
from collections import deque


class BitBuffer:
    """
    A utility class that makes handling bits (and not bytes) easy.
    """
    __slots__ = [
        # Since the buffer is designed to hold lots of bits, we'll hold them as a deque of integers (a deque allows us
        # to store data non-consecutively, and the integer type allows easy bit manipulation):
        '__saved_data',

        # The current int we are writing to (it is still not in the `saved_data` attribute). Will be None if the object
        # was just instantiated or if the previous `current_int` was just pushed to the deque:
        '__current_int',

        # The index of the bit in 'current_int' that will be written to in the next method call. Notice that it
        # points to the bit that you get if you call `(current_int >> (31 - bit_idx)) & 1`. This is done in order to
        # preserve the order of bit insertions:
        '__bit_idx'
    ]

    def __init__(self) -> 'BitBuffer':
        """
        Creates an empty Bitbuffer.
        """
        # Initialize everything:
        self.__saved_data: deque[int] = deque()
        self.__current_int: Optional[int] = None
        self.__bit_idx = 0

    def insert_bit(self, bit: int) -> 'BitBuffer':
        """
        Inserts the first (least significant) bit of the given integer into the object.
        :param bit: An integer whose first bit will be inserted into the object. Although this value is an integer,
                    it must equal either 0 or 1.
        :return: The current BitBuffer object, in order to support the builder pattern.
        :raises TypeError: If bit isn't of type int.
        :raises ValueError: If the bit given is not 1 nor 0.
        """
        # Type and value check:
        if not isinstance(bit, int):
            raise TypeError(f"Expected int, got {type(bit)} instead")
        elif bit != 0 and bit != 1:
            raise ValueError(f"Bit value must equal 0 or 1, got {bit} instead")

        # Check if we need to replace the current integer:
        if self.__current_int is None:
            self.__current_int = 0

        # Insert the bit:
        self.__current_int |= (bit & 1) << (31 - self.__bit_idx)
        self.__bit_idx += 1

        # In case we wrote enough to fill the entire integer, insert it to the deque and reset it:
        if self.__bit_idx == 32:
            self.__save_current_int()

        return self

    def insert_byte(self, byte: bytes) -> 'BitBuffer':
        """
        Inserts a single byte into the bitbuffer.
        Note that, in terms of ordering, the byte's most significant bit is inserted first, and the least significant
        last.
        :param byte: A bytes object holding A SINGLE byte. That byte value will be inserted into the buffer.
        :return: The current BitBuffer object, in order to support the builder pattern.
        :raises TypeError: If the given byte value is not of type `bytes`.
        :raises ValueError: If the bytes object holds more than one byte.
        """
        # Type and value check:
        if not isinstance(byte, bytes):
            raise TypeError(f"Expected bytes, got {type(byte)} instead")
        elif len(byte) != 1:
            raise ValueError(f"Bytes object must hold a single byte - got {len(byte)} instead")

        # Convert to integer:
        byte_val: int = byte[0]

        # Check if we need to replace the current integer:
        if self.__current_int is None:
            self.__current_int = 0

        # Insert as many bits as possible into the current integer:
        free_bits = 32 - self.__bit_idx
        if free_bits > 8:
            self.__current_int |= byte_val << (free_bits - 8)
            self.__bit_idx += 8
        else:
            self.__current_int |= byte_val >> (8 - free_bits)

            # Save the current integer and add the remaining bits to the next one:
            self.__save_current_int()
            self.__current_int = byte_val << (24 + free_bits)
            self.__bit_idx = 8 - free_bits

        return self

    def __save_current_int(self) -> None:
        """
        Saves the current integer in the deque. Only use if the integer is full.
        """
        self.__saved_data.append(self.__current_int)
        self.__current_int = None
        self.__bit_idx = 0

    def __bytes__(self):
        """
        Extracts the bits saved in the buffer as a bytes object. The order in which the bits were inserted into the
        object is preserved.
        :return: A bytes object containing the bits in the object.
        """
        # Calculate the amount of bytes needed beforehand:
        saved_ints_bytes_count = 4 * len(self.__saved_data)
        current_int_bytes_count = (self.__bit_idx + 7) // 8
        bytes_needed = saved_ints_bytes_count + current_int_bytes_count

        # Create a bytearray with this size:
        stored_bits = bytearray(bytes_needed)

        # Insert the saved integers first (their bits are already ordered according to user insertions):
        for int_idx, saved_int in enumerate(self.__saved_data):
            # An integer has 4 bytes:
            for i in range(4):
                stored_bits[int_idx * 4 + i] = BitBuffer.__get_byte_from_int(saved_int, i)

        # Add the current int as well (bit_idx will be 0 if current_int is None and the loop won't execute):
        for i in range(current_int_bytes_count):
            stored_bits[saved_ints_bytes_count + i] = BitBuffer.__get_byte_from_int(self.__current_int, i)

        return bytes(stored_bits)

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
