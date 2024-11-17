from collections import Counter
from compressors import Compressor


class ArithmeticCompressor(Compressor):
    @staticmethod
    def get_cumulative_frequency_ranges(input_data: bytes) -> list[tuple[int, int]]:
        """
        Given a bytes object representing input data, this function computes and returns the cumulative frequency ranges
        for each byte value in the input data.

        The cumulative frequency range for a byte value 'i' is the interval [low, high), where:
        - 'low' is the cumulative frequency of byte value 'i-1' (or 0 if 'i' is 0).
        - 'high' is the cumulative frequency of byte value 'i'.

        The cumulative frequency of a byte value is defined as the sum of the frequencies of all byte values smaller
        than or equal to that byte value. The cumulative frequency range provides a way to map each byte to a specific
        interval in the range [0, total frequency of all bytes].

        :param input_data: A bytes object containing the input data. The frequency of each byte value is calculated
                           to determine the cumulative frequency ranges.
        :return: A list of length 256, where each element at index 'i' is a tuple (low, high).
                 The tuple represents the cumulative frequency range for byte value 'i'.
                 - 'low' is the cumulative frequency of byte 'i-1' (or 0 for byte 0).
                 - 'high' is the cumulative frequency of byte 'i'.
        """
        # Count the occurrence of every byte value:
        counter = Counter(input_data)

        # Form the cumulative frequencies list:
        cumulative_frequencies: list[tuple[int, int]] = [(0, 0)] * 256
        cumulative_frequencies[0] = 0, counter[0]
        for byte_val in range(1, len(cumulative_frequencies)):
            prev_cum = cumulative_frequencies[byte_val - 1]
            cumulative_frequencies[byte_val] = prev_cum[1], prev_cum[1] + counter[byte_val]

        return cumulative_frequencies

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on arithmetic coding.
        :param input_data: The bytes that will be encoded.
        :return: A compressed version of 'input_data'.
        """
        # Get the cumulative frequency of each byte value:
        cumulative_frequencies: list[tuple[int, int]] = ArithmeticCompressor.get_cumulative_frequency_ranges(input_data)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
