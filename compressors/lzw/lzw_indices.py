from collections import deque
from compressors.lzw.encoding_dict import EncodingDict
from compressors.lzw.memory_limits import OutOfMemoryStrategy


class EncodingIndices:
    """
    A class encapsulating the logic behind converting input data into indices inside an LZW dictionary.
    """
    __slots__ = (
        # The indices of the encoded data inside the lzw dictionary:
        '__indices',
    )

    def __init__(self, input_data: bytes, max_dict_size: int, memory_strategy: OutOfMemoryStrategy) -> 'EncodingIndices':
        """
        Parses the input data into encoding indices inside an LZW dictionary.
        :param input_data: The input that will be compressed into indices.
        :param max_dict_size: The maximum amount of entries the LZW dictionary can contain.
        :param memory_strategy: In case encoding the data requires more entries than 'max_dict_size' this parameter
                                informs the method which actions to take.
        :raises TooManyEncodingsException: If not enough memory was given to the encoding dictionary
                                           in order to complete the algorithm, and OutOfMemoryStrategy.ABORT was
                                           provided as an argument.
        """
        # Initialize the dictionary:
        lzw_dict: EncodingDict = EncodingDict(max_dict_size)

        # The starting index of the slice that matches a dictionary value:
        matching_start_idx: int = 0
        self.__indices: deque[int] = deque()

        for i in range(1, len(input_data)):
            # Get the current data slice:
            current_data = input_data[matching_start_idx:i + 1]

            # If it's not in the dictionary, insert the index of the previous slice, and
            # add the new slice to the dictionary:
            if not lzw_dict.contains_key(current_data):
                prev_matching = input_data[matching_start_idx:i]
                self.__indices.append(lzw_dict[prev_matching])

                lzw_dict.try_insert(current_data, memory_strategy)
                matching_start_idx = i

        # In case the end of the input matched a dictionary value, the loop didn't append it:
        forgotten = input_data[matching_start_idx:]
        if len(forgotten) > 0:
            self.__indices.append(lzw_dict[forgotten])

    @property
    def indices(self) -> deque[int]:
        return self.__indices

    def get_padded_bytes(self) -> bytes:
        """
        When compressing the indices, the decompression algorithm needs to know where an index starts and end.
        One approach is to decide on a fixed size for all of them, however this wastes space.
        The current method pads the indices as bytes in the following way:
            Before every index, an extra byte is added. This byte will tell the decompression algorithm
            how many bytes to read for the next index.
        This method adds only one extra byte per index, which is more efficient than the other approach mentioned above.
        :return: A bytes object containing the indices in the object, along with extra bytes to allow the decompression
                 algorithm to read the indices.
        """
        # For every index, extract only its necessary bytes (get rid of unnecessary 0 byts):
        def get_important_bytes(n: int) -> bytes:
            if n == 0:
                return bytes(1)
            important_bytes = []
            while n > 0:
                important_bytes.append(n & 0xFF)
                n >>= 8
            return bytes(important_bytes)  # Most significant byte last (little endian)
        necessary_indices_bytes = map(get_important_bytes, self.indices)

        # Add an extra byte for length:
        padded_indices = map(lambda index_bytes: bytes([len(index_bytes)]) + index_bytes, necessary_indices_bytes)

        # Concatenate it all:
        return b''.join(padded_indices)
