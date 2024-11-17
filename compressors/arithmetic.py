from collections import Counter
from compressors import Compressor


class ArithmeticCompressor(Compressor):
    @staticmethod
    def get_cumulative_frequencies(input_data: bytes) -> list[int]:
        """
        Given a bytes object representing input data, the function returns a list containing the cumulative frequency
        of each byte value in the input data.
        Cumulative frequency is defined as the sum of the frequency of the current byte value in the input data, and the
        cumulative frequency of byte values smaller than it.
        :param input_data: A collection of byte values. The frequency of each byte value will be recorded to compute
                           the cumulative frequency.
        :return: A list of length 256. Each element at index 'i' in that list is the cumulative frequency of the byte
                 value 'i'. By definition of cumulative frequency, the last element will always equal the length of
                 'input_data'.
        """
        # Count the occurrence of every byte value:
        counter = Counter(input_data)

        # Form the cumulative frequencies list:
        cumulative_frequencies = [0] * 256
        cumulative_frequencies[0] = counter[0]
        for byte_val in range(1, len(cumulative_frequencies)):
            cumulative_frequencies[byte_val] = counter[byte_val] + cumulative_frequencies[byte_val - 1]

        return cumulative_frequencies

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on arithmetic coding.
        :param input_data: The bytes that will be encoded.
        :return: A compressed version of 'input_data'.
        """
        # Get the cumulative frequency of each byte value:
        cumulative_frequencies: list[int] = ArithmeticCompressor.get_cumulative_frequencies(input_data)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
