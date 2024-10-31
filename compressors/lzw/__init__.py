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

    def __get_encoder_indices(self, input_data: bytes) -> list[int]:
        """
        Parses the input data and converts it to a list of indices inside an encoder dictionary.
        Calling this method will change the encoder dictionary saved in the object, as previous
        indices cannot be used on the new data.
        :param input_data: The input data before being compressed.
        :return: A list of indices inside an encoder dictionary.
        :raises TooManyEncodingsException: If not enough memory was given to the encoding dictionary
                                           in order to complete the algorithm.
        """
        # Clear previous indices:
        self.__encoder_dict.clear()

        # The starting index of the slice that matches a dictionary value:
        matching_start_idx: int = 0
        output: list[int] = []

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

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on the Lempel-Ziv-Welch algorithm.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed by the LZW algorithms.
        :raises TooManyEncodingsException: If not enough memory was given to the encoding dictionary
                                           in order to complete the algorithm.
        """
        pass

    def decode(self, compressed_data: bytes) -> bytes:
        pass
