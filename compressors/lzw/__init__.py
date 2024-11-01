from typing import Generator
from collections import deque
from compressors import Compressor
from .encoding_dict import EncodingDict, TooManyEncodingsException


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

    @staticmethod
    def encoded_indices_iterator(compressed_data: bytes) -> Generator[int, None, None]:
        """
        Provides a generator iterating through the compressed data and removing the padding from it.
        The generator will extract the encoded indices in the data.
        :param compressed_data: Data that was compressed using the LzwCompressor class.
        :raises ValueError: If either a length byte has a non-positive value, or there aren't enough bytes
                            following said length byte.
        """
        byte_idx = 0
        while byte_idx < len(compressed_data):
            # Get the length byte:
            index_len = compressed_data[byte_idx]
            byte_idx += 1

            # Validate length:
            if index_len <= 0:
                raise ValueError(f'Malformed compressed data: Invalid value for length byte ({index_len})')
            elif byte_idx + index_len > len(compressed_data):
                raise ValueError(f'Malformed compressed data: Not enough bytes for index')

            # Convert the next bytes to integer (remember big indian - significant byte first):
            index = int.from_bytes(compressed_data[byte_idx:byte_idx + index_len], byteorder='big')

            # Move the byte index the rest of the bytes:
            byte_idx += index_len
            yield index

    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the given compressed data according to the LZW algorithm.
        Certain assumptions are made about the given data, so this function should only be
        used on data that was compressed using the `encode` method in the LzwCompressor class.
        :param compressed_data: Data that was compressed using the LzwCompressor class.
        :return: The decompressed bytes of the given data.
        :raises ValueError: If the data is not padded correctly and reading indices from it fails.
        :raises TooManyEncodingsException: If in order to decompress the data, the number of entries
                                           in the decoder dictionary exceeds the maximum.
        """
        # The decoding dictionary is easier so just use a normal dictionary (and a keys set for faster
        # lookup):
        unoccupied_idx = 256
        keys: set[int] = set()
        decoder_dict: dict[int, bytes] = {}

        # Prepare the output in a deque for memory optimization:
        output: deque[bytes] = deque()
        last_emitted: bytes = b''

        for encoded_idx in LzwCompressor.encoded_indices_iterator(compressed_data):
            # Check for memory limitations:
            if encoded_idx - 256 > self.__encoder_dict.max_size:
                raise TooManyEncodingsException()

            # Check if the index is in the dictionary (smaller than unoccupied_idx), or is ascii:
            is_ascii, is_in_dict = encoded_idx < 256, encoded_idx < unoccupied_idx
            if is_ascii or is_in_dict:
                # Get the corresponding bytes and add them to the output:
                decoded = bytes([encoded_idx]) if is_ascii else decoder_dict[encoded_idx]
                output.append(decoded)

                # Add the last emitted bytes object along with the first byte of the decoded
                # bytes to the dictionary (only if the result is not an ascii value!):
                if len(last_emitted) > 0:
                    decoder_dict[unoccupied_idx] = last_emitted + bytes([decoded[0]])
                    keys.add(unoccupied_idx)
                    unoccupied_idx += 1

                # Switch the last emitted:
                last_emitted = decoded

            # It's ok if the index is completely new, but make sure it is legit and the last emitted
            # bytes object isn't empty (in a correct compression, first index is always below 256,
            # but the index reader may read an invalid index):
            elif len(last_emitted) == 0:
                raise ValueError('Malformed compressed data: Invalid index value at the start')

            # If the index is completely new, add the first byte of the last emitted bytes to itself,
            # and add the result to both the dictionary and the output:
            else:
                last_emitted = last_emitted + bytes([last_emitted[0]])
                output.append(last_emitted)

                decoder_dict[unoccupied_idx] = last_emitted
                keys.add(unoccupied_idx)
                unoccupied_idx += 1

        return b''.join(output)
