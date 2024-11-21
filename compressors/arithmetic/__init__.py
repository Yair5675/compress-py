import itertools
from compressors import Compressor
from util.bitbuffer import BitBuffer
from compressors.arithmetic.interval_state import IntervalState
from compressors.arithmetic.bits_system import BitsSystem, InsufficientValueRange


class ArithmeticCompressor(Compressor):

    __slots__ = (
        # Boundaries of the current interval during compression/decompression:
        'low', 'high',

        # Number of bits that were removed to prevent a near-convergence situation:
        'near_conv_count',

        # A list of the cumulative frequencies of all byte values plus the EOF value in the input data.
        # The range defined for a byte value 'i' is the element at index i, up until the element at index i + 1.
        # The EOF value is an exception, because its range is the second to last element, up until the last element.
        # The last element represents the total frequency:
        'cum_freqs',

        # The bits system the calculations will be made in:
        'bits_system'
    )

    # An EOF value, guaranteed not to be a byte value:
    EOF = 0xFFF

    def __init__(self) -> 'ArithmeticCompressor':
        # For now, just initialize a 32-bit system:
        self.bits_system = BitsSystem(32)

        # Initialize equal probability:
        self.__init_equal_probs()

    def __init_equal_probs(self) -> None:
        """
        Initializes the cumulative frequencies list to represent equal probabilities for each byte value (and the EOF
        value) in an input.
        """
        # Check that the bits system is enough to represent 257 values:
        if self.bits_system.MAX_CODE < 257:
            raise InsufficientValueRange(257)

        # Assign equal frequencies to all values:
        self.cum_freqs: tuple[int] = tuple(i for i in range(258))

    def get_cum_interval(self, value: int) -> tuple[int, int]:
        """
        Calculates the cumulative frequency interval corresponding to the given value.
        If a value is a possible byte value (i.e: 0 <= value <= 0xFF), its interval is returned. If value is
        ArithmeticCompressor.EOF, its interval is returned. If value equals any other value, a ValueError is raised.
        :param value: The byte value or EOF value whose probability interval is needed.
        :return: The interval of the current value, represented as a tuple of [start_cum, end_cum).
        :raises ValueError: If value is neither a byte value (0 <= value <= 0xFF) nor ArithmeticCompressor.EOF.
        """
        if 0 <= value <= 0xFF:
            return self.cum_freqs[value], self.cum_freqs[value + 1]
        elif value == ArithmeticCompressor.EOF:
            return self.cum_freqs[-2], self.cum_freqs[-1]
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
        # Get the cumulative frequency interval corresponding to `byte_val`:
        cum_interval: tuple[int, int] = self.get_cum_interval(byte_val)

        # Calculate interval width:
        width: int = self.high - self.low + 1

        # Update low and high:
        total_freq: int = self.cum_freqs[-1]
        self.high = (self.low - 1 + width * cum_interval[1] // total_freq) & 0xFF
        self.low = (self.low + width * cum_interval[0] // total_freq) & 0xFF

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
        match state := IntervalState.get_state(self.low, self.high, self.bits_system):
            case IntervalState.CONVERGING_0 | IntervalState.CONVERGING_1:
                # Add matching bit:
                matching_bit = 1 if state is IntervalState.CONVERGING_1 else 0
                self.add_bit_and_pending(matching_bit, output)

                # Remove it:
                self.low = (self.low << 1) & self.bits_system.MAX_CODE
                self.high = ((self.high << 1) | 1) & self.bits_system.MAX_CODE

                # Reset near-convergence bits:
                self.near_conv_count = 0

            # Handle near-convergence situations:
            case IntervalState.NEAR_CONVERGENCE:
                # Increment pending, remove the second MSB and shift in new LSBs (0 for low, 1 for high):
                self.near_conv_count += 1
                mask = self.bits_system.MAX_CODE >> 2  # Mask deletes first and second MSBs
                self.low = (self.low & mask) << 1
                self.high = ((self.high & mask) << 1) | 0x81

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
        self.low, self.high, self.near_conv_count = 0, self.bits_system.MAX_CODE, 0

        # Output buffer:
        output_buffer: BitBuffer = BitBuffer()

        # Loop over input data, and add an EOF at the end:
        for byte_val in itertools.chain(input_data, (ArithmeticCompressor.EOF,)):
            # Calculate new interval based on the current byte value:
            self.calc_new_boundary(byte_val)

            # Process interval state:
            while IntervalState.get_state(self.low, self.high, self.bits_system) is not IntervalState.NON_CONVERGING:
                self.process_interval_state(output_buffer)

        # When the loop exits, the possible boundaries are:
        # - [01yyy, 11xxx)
        # - [00yyy, 11xxx)
        # - [00yyy, 10xxx)
        # So we must insert '01' if low is '00', and '10' if low is '01'. Along with those, any pending near-convergence
        # bits must be inserted as well. A simple way of doing it is just adding 1 to the near-convergence counter and
        # insert the value of low's second MSB:
        self.near_conv_count += 1
        self.add_bit_and_pending(self.low >> (self.bits_system.BITS_USED - 2), output_buffer)

        # The padding that BitBuffer appends to the data is ok. Since it is only zeroes, it does not change the number
        # that the compressor had produced:
        return bytes(output_buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        pass
