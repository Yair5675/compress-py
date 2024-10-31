from collections import deque
from compressors import Compressor
from encoding_dict import EncodingDict

class LzwCompressor(Compressor):
    __slots__ = [
        # The dictionary used for encoding data:
        '__encoder_dict'
    ]

    def __init__(self, max_dict_size: int):
        # Set the encoder dictionary:
        self.__encoder_dict = EncodingDict(max_dict_size)

    def __get_encoder_indices(self, input_data: bytes) -> deque[int]:
        """
        Parses the input data and converts it to a list of indices inside an encoder dictionary.
        Calling this method will change the encoder dictionary saved in the object, as previous
        indices cannot be used on the new data.
        :param input_data: The input data before being compressed.
        :return: A deque of indices inside an encoder dictionary.
        :raises TooManyEncodingsException: If not enough memory was given to the encoding dictionary
                                           in order to complete the algorithm.
        """
        # Clear previous indices:
        self.__encoder_dict.clear()

        # The starting index of the slice that matches a dictionary value:
        matching_start_idx: int = 0
        output: deque[int] = deque()

        for i in range(1, len(input_data)):
            # Get the current data slice:
            current_data = input_data[matching_start_idx:i + 1]

            # If it's not in the dictionary, insert the index of the previous slice, and
            # add the new slice to the dictionary:
            if not self.__encoder_dict.contains_key(current_data):
                prev_matching = input_data[matching_start_idx:i]
                output.append(self.__encoder_dict[prev_matching])

                self.__encoder_dict.insert(current_data)  # This can raise a memory exception
                matching_start_idx = i

        # In case the end of the input matched a dictionary value, the loop didn't append it:
        forgotten = input_data[matching_start_idx:]
        if len(forgotten) > 0:
            output.append(self.__encoder_dict[forgotten])

        return output

    @staticmethod
    def __pad_encoded_indices(indices: deque[int]) -> bytes:
        """
        When compressing the indices, the decompression algorithm needs to know where an index starts and end.
        One approach is to decide on a fixed size for all of them, however this wastes space.
        The current function pads the indices in the following way:
            Before every index, an extra byte is added. This byte will tell the decompression algorithm
            how many bytes to read for the next index.
        This method adds only one extra byte per index, which is more efficient than the other approach
        mentioned above.
        :param indices: A list of the indices that will be padded and turned into a bytes object.
        :return: A bytes object containing the given indices along with extra bytes to allow the decompression
                 algorithm to read the indices.
        """
        # For every index, extract only its necessary bytes (get rid of unnecessary 0 bits):
        def get_important_bytes(n: int) -> bytes:
            if n == 0:
                return bytes(1)
            important_bytes = []
            while n > 0:
                important_bytes.append(n & 0xFF)
                n >>= 8
            return bytes(reversed(important_bytes))  # Most significant byte first
        necessary_indices_bytes = map(get_important_bytes, indices)

        # Add an extra byte for length:
        padded_indices = map(lambda index_bytes: bytes([len(index_bytes)]) + index_bytes, necessary_indices_bytes)

        # Concatenate it all:
        return b''.join(padded_indices)

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on the Lempel-Ziv-Welch algorithm.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed by the LZW algorithms.
        :raises TypeError: If the input data isn't a `bytes` object.
        :raises TooManyEncodingsException: If not enough memory was given to the encoding dictionary
                                           in order to complete the algorithm.
        """
        # Validate type:
        if not isinstance(input_data, bytes):
            raise TypeError(f'Expected type bytes, got {type(input_data)} instead')

        # Parse indices:
        indices = self.__get_encoder_indices(input_data)

        # Pad and return them:
        return LzwCompressor.__pad_encoded_indices(indices)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
