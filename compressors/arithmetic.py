from collections import namedtuple
from compressors import Compressor

# A type representing a probability interval inside the arithmetic compressor. Since we are working with integer
# math only, it will be represented as a cumulative frequency, and total cumulative frequency. True probability
# can be calculated as `prob_0 = start_cum // tot_cum, prob_1 = end_cum // tot_cum`:
ProbabilityInterval = namedtuple('ProbabilityInterval', (
    # Cumulative frequency up until this interval:
    'start_cum',
    # Cumulative frequency up until this interval, including it:
    'end_cum',
    # Cumulative frequency of all intervals:
    'tot_cum'
))


class ArithmeticCompressor(Compressor):

    __slots__ = (
        # The probability intervals that define the arithmetic compression:
        'prob_intervals',
    )

    def __init__(self) -> 'ArithmeticCompressor':
        self.__init_equal_probs()

    def __init_equal_probs(self) -> None:
        """
        Assigns a list of probability intervals to attribute 'prob_intervals'.
        The assigned intervals are equal in length, which means the compressor assumes each byte value is equally
        likely. Granted, adaptive probability intervals may produce better compression efficiency.
        The intervals list will be of length 257:
            - First 256 elements represent the intervals corresponding to all byte values.
            - Last element is an additional 'EOF' value.
        """
        # Total cumulative frequency is 257:
        tot_cum = 257

        # Build probability intervals with equal probabilities:
        self.prob_intervals: tuple[ProbabilityInterval] = tuple(
            ProbabilityInterval(i, i + 1, tot_cum) for i in range(257)
        )

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on arithmetic coding.
        :param input_data: The bytes that will be encoded.
        :return: A compressed version of 'input_data'.
        """
        pass

    def decode(self, compressed_data: bytes) -> bytes:
        pass
