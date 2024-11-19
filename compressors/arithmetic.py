import itertools
from enum import Enum, auto
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


class IntervalState(Enum):
    """
    During compression/decompression, the interval boundaries 'low' and 'high' determine the output. Their state
    determines the outputted bit. This enum contains every state those boundaries can be in:
    """
    # Both low and high's MSB is 0:
    CONVERGING_0 = auto()

    # Both low and high's MSB is 1:
    CONVERGING_1 = auto()

    # Near-convergence (low >= one fourth, and high < three fourths):
    NEAR_CONVERGENCE = auto()

    # Not converging (none of the above):
    NON_CONVERGING = auto()

    def is_converging(self) -> bool:
        """
        Checks whether the current interval state is CONVERGING_0 or CONVERGING_1.
        :return: True if self is a converging variant of IntervalState, false otherwise.
        """
        return self is IntervalState.CONVERGING_0 or self is IntervalState.CONVERGING_1

    @staticmethod
    def get_state(low: int, high: int) -> 'IntervalState':
        # Check convergence:
        if low >= 0x80:
            return IntervalState.CONVERGING_1
        elif high < 0x80:
            return IntervalState.CONVERGING_0
        # Check near-convergence:
        elif low >= 0x40 and high < 0xC0:
            return IntervalState.NEAR_CONVERGENCE
        # Default - non-converging:
        else:
            return IntervalState.NON_CONVERGING


class ArithmeticCompressor(Compressor):

    __slots__ = (
        # Boundaries of the current interval during compression/decompression:
        'low', 'high',

        # Number of bits that were removed to prevent a near-convergence situation:
        'near_conv_count',

        # The probability intervals that define the arithmetic compression:
        'prob_intervals'
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

    def add_bit_and_pending(self, bit: int, output: BitBuffer) -> None:
        """
        Inserts the current bit to the output, along with any pending bits from previous occurrences of
        near-convergence.
        :param bit: A bit that will be added to the output.
        :param output: The output buffer that the bits will be written to.
        """
        # Add the bit:
        output.insert_bits(bit, 1)

        # If there are any pending, add the inverted bit `pending` times:
        if self.near_conv_count > 0:
            inverted_bit = 0 if bit == 1 else 0xFFFFFFFF

            # BitBuffer only inserts the first 32 bits, so just in case future versions can have over 32
            # near-convergence bits, add them in groups of 32:
            for _ in range(self.near_conv_count // 32):
                output.insert_bits(inverted_bit, 32)
            if (remaining_bits := self.near_conv_count % 32) > 0:
                output.insert_bits(inverted_bit, remaining_bits)

    def calc_new_boundary(self, byte_val: int) -> None:
        """
        Internally updates `low` and `high` based on the current byte value and the internal probability intervals.
        :param byte_val: The current byte value, will determine the new interval [low, high).
        """
        # Get the probability interval corresponding to `byte_val`:
        prob_interval: ProbabilityInterval = self.get_prob_interval(byte_val)

        # Calculate interval width:
        width: int = self.high - self.low + 1

        # Update low and high:
        self.high = (self.low - 1 + width * prob_interval.end_cum // prob_interval.tot_cum) & 0xFF
        self.low = (self.low + width * prob_interval.start_cum // prob_interval.tot_cum) & 0xFF

    def process_interval_state(self, output: BitBuffer) -> None:
        """
        The method calculates the current state of the interval [low, high), adds bits to `output` if needed, and
        internally calculates new values for 'low' and 'high'.
        The function handles those two cases:
            1) Matching MSBs - The function will output the matching MSB to output (along with pending bits from
                               near-convergence situations), and will remove them from low and high.
            2) Near-convergence - The function will increment the counter of pending near-convergence bits, and will
                                  remove the second MSBs from `low` and `high`, freeing their bits.
        If the interval state is NON_CONVERGING, nothing will be done.
        :param output: The output buffer that, if needed, bits will be inserted to.
        """
        # Check state:
        match state := IntervalState.get_state(self.low, self.high):
            case IntervalState.CONVERGING_0 | IntervalState.CONVERGING_1:
                # Add matching bit:
                matching_bit = 1 if state is IntervalState.CONVERGING_1 else 0
                self.add_bit_and_pending(matching_bit, output)

                # Remove it:
                self.low = (self.low << 1) & 0xFF
                self.high = ((self.high << 1) | 1) & 0xFF

                # Reset near-convergence bits:
                self.near_conv_count = 0

            # Handle near-convergence situations:
            case IntervalState.NEAR_CONVERGENCE:
                # Increment pending, remove the second MSB and shift in new LSBs (0 for low, 1 for high):
                self.near_conv_count += 1
                self.low = (self.low & 0x3F) << 1
                self.high = ((self.high & 0x3F) << 1) | 0x81

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on arithmetic coding.
        :param input_data: The bytes that will be encoded.
        :return: A compressed version of 'input_data'.
        """
        # Empty edge-case:
        if len(input_data) == 0:
            return bytes()

        # Initialize interval boundaries and near-convergence bits:
        self.low, self.high, self.near_conv_count = 0, 0xFF, 0

        # Output buffer:
        output_buffer: BitBuffer = BitBuffer()

        # Loop over input data, and add an EOF at the end:
        for byte_val in itertools.chain(input_data, (ArithmeticCompressor.EOF,)):
            # Calculate new interval based on the current byte value:
            self.calc_new_boundary(byte_val)

            # Process interval state:
            while IntervalState.get_state(self.low, self.high) is not IntervalState.NON_CONVERGING:
                self.process_interval_state(output_buffer)

        # When the loop exits, the possible boundaries are:
        # - [01yyy, 11xxx)
        # - [00yyy, 11xxx)
        # - [00yyy, 10xxx)
        # So we must insert '01' if low is '00', and '10' if low is '01'. Along with those, any pending near-convergence
        # bits must be inserted as well. A simple way of doing it is just adding 1 to the near-convergence counter and
        # insert the value of low's second MSB:
        self.near_conv_count += 1
        self.add_bit_and_pending(self.low >> 6, output_buffer)

        # The padding that BitBuffer appends to the data is ok. Since it is only zeroes, it does not change the number
        # that the compressor had produced:
        return bytes(output_buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
