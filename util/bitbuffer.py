from collections import deque

# In order to enforce the assumption that all integers have 32 bits, 'and' every left-shift result with this mask to
# receive the first 32 bits only:
FULL_INT_MASK = 0xFFFFFFFF


class BitBuffer:
    """
    A utility class that makes handling bits (and not bytes) easy.
    """
    __slots__ = [
        # Since the buffer is designed to hold lots of bits, we'll hold them as a deque of integers (a deque allows us
        # to store data non-consecutively, and the integer type allows easy bit manipulation):
        '__saved_data',

        # The current int we are writing to (it is still not in the `saved_data` attribute):
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
        :param bits_num: The number of bits to extract from the integer. Must be in range(1, 33).
        :return: The current BitBuffer object, in order to support the builder pattern.
        """
        # Extract the necessary bits only:
        bits_container &= (1 << bits_num) - 1

        # Insert as many bits as possible into the current integer:
        free_bits = 32 - self.__bit_idx
        if free_bits > bits_num:
            self.__current_int |= (bits_container << (free_bits - bits_num)) & FULL_INT_MASK
            self.__bit_idx += bits_num
        else:
            # Insert what you can into the current integer:
            next_int_bits_count = bits_num - free_bits
            self.__current_int |= bits_container >> next_int_bits_count

            # Save the current integer and add the remaining bits to the next one:
            self.__save_current_int()
            self.__current_int = (bits_container << (32 - next_int_bits_count)) & FULL_INT_MASK
            self.__bit_idx = bits_num - free_bits

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
        return 32 * len(self.__saved_data) + self.__bit_idx

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

        # Add the current int as well:
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
