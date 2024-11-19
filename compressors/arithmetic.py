from collections import namedtuple
from compressors import Compressor
from util.bitbuffer import BitBuffer

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

    # An EOF value, guaranteed not to be a byte value:
    EOF = 0xFFF

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

    def get_prob_interval(self, value: int) -> ProbabilityInterval:
        """
        Calculates the probability interval corresponding to the given value.
        If a value is a possible byte value (i.e: 0 <= value <= 0xFF), its interval is returned. If value is
        ArithmeticCompressor.EOF, its interval is returned. If value equals any other value, a ValueError is raised.
        :param value: The byte value or EOF value whose probability interval is needed.
        :return: The probability interval of the provided value.
        :raises ValueError: If value is neither a byte value (0 <= value <= 0xFF) nor ArithmeticCompressor.EOF.
        """
        if 0 <= value <= 0xFF:
            return self.prob_intervals[value]
        elif value == ArithmeticCompressor.EOF:
            return self.prob_intervals[-1]
        else:
            raise ValueError(f'Value is neither a byte value nor EOF (but instead {value})')

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on arithmetic coding.
        :param input_data: The bytes that will be encoded.
        :return: A compressed version of 'input_data'.
        """
        # All stored values are 8 bits, for simplicity (it may be changed later)
        low, high = 0, 0xFF

        # Output buffer:
        output_buffer: BitBuffer = BitBuffer()

        # Loop over input data:
        for byte_val in input_data:
            # Calculate current interval's width:
            width: int = high - low + 1

            # Calculate new interval based on the current byte value:
            prob_interval: ProbabilityInterval = self.get_prob_interval(byte_val)
            high = low + width * prob_interval.end_cum // prob_interval.tot_cum
            low = low + width * prob_interval.start_cum // prob_interval.tot_cum

            # TODO: Handle similar MSBs
            # TODO: Handle near-convergence situations
            # TODO: Add an EOF

        # The padding that BitBuffer appends to the data is ok. Since it is only zeroes, it does not change the number
        # that the compressor had produced:
        return bytes(output_buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
