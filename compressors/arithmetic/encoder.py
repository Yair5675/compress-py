import itertools
from collections import defaultdict
from util.bitbuffer import BitBuffer
from compressors.arithmetic.bits_system import BitsSystem
from compressors.arithmetic.interval_state import IntervalState


class Encoder:
    __slots__ = (
        # Current interval's starting value and length:
        '__low', '__width',

        # Bits system used when holding/calculating values:
        'bits_system',

        # Special EOF symbol (mustn't be a valid byte value):
        'eof',

        # The number of pending bits from near-convergence situations during encoding:
        'pending_bits',

        # Cumulative Frequency Intervals - a mapping between an input value and its interval inside the total cumulative
        # frequency of the input:
        'cfi',

        # Total frequency of the input data:
        'total_freq'
    )

    def __init__(self, eof: int, bits_system: BitsSystem) -> 'Encoder':
        self.bits_system = bits_system
        self.eof = eof

    @property
    def low(self):
        return self.__low

    @low.setter
    def low(self, value):
        self.__low = value & self.bits_system.MAX_CODE

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, value):
        self.__width = value & self.bits_system.MAX_CODE

    def init_cum_freqs(self, input_data: bytes) -> None:
        """
        Initializes the cumulative frequency dictionary and the total frequency attributes according to the input data.
        """
        # Count all byte value occurrences, but limit the maximum frequency to have half the bits used by the bits
        # system (ensuring all byte values can always be encoded with no interval overlap):
        TOTAL_FREQ_LIMIT = 1 << (self.bits_system.BITS_USED // 2)
        FREQ_PER_BYTE_LIMIT = TOTAL_FREQ_LIMIT // 256

        counter: defaultdict[int, int] = defaultdict(int)
        for byte_val in input_data:
            if counter[byte_val] < FREQ_PER_BYTE_LIMIT:
                counter[byte_val] = counter[byte_val] + 1

        # Add the EOF value:
        counter[self.eof] = 1

        # Loop over the elements, and add their cumulative frequencies inside the dictionary:
        prev_cum_freq = 0
        self.cfi: dict[int, tuple[int, int]] = {}
        for value, freq in counter.items():
            self.cfi[value] = prev_cum_freq, prev_cum_freq + freq
            prev_cum_freq += freq

        # The total frequency is now saved in prev_cum_freq:
        self.total_freq = prev_cum_freq

    def update_interval(self, input_value: int) -> None:
        """
        Updates the 'low' and 'width' attributes of the object based on the input value.
        This essentially updates the currently saved interval to match the input value.
        :param input_value: A byte value or EOF value whose CFI will determine the next interval.
        """
        # Get the CFI of the input value:
        cum_interval = self.cfi[input_value]

        # Update low and width:
        self.low += self.width * cum_interval[0] // self.total_freq
        self.width = self.width * cum_interval[1] // self.total_freq - self.width * cum_interval[0] // self.total_freq

    def insert_with_pending(self, bit: int, output: BitBuffer) -> None:
        # Insert the bit:
        output.insert_bits(bit, 1)

        # Insert pending bits in groups of 32:
        bits_to_insert = 0 if bit else 0xFFFFFFFF
        for _ in range(self.pending_bits // 32):
            output.insert_bits(bits_to_insert, 32)
        if self.pending_bits % 32 > 0:
            output.insert_bits(bits_to_insert, self.pending_bits % 32)

        # Clear the pending bits:
        self.pending_bits = 0

    def process_state(self, interval_state: IntervalState, output: BitBuffer) -> None:
        """
        Changes the current interval and outputs bits to the output buffer according to the provided interval state.
        The method assumes `interval_state` is not IntervalState.NON_CONVERGING.
        :param interval_state: The state according to which the current interval will change, and may result in bits
                               outputted to the output buffer.
                               Cannot be IntervalState.NON_CONVERGING.
        :param output: The output buffer. If any bits need to be outputted, they will be added to this buffer.
        """
        match interval_state:
            # In case of a matching MSB, output it and make sure `low` is less than half:
            case IntervalState.CONVERGING_0:
                self.insert_with_pending(0, output)
            case IntervalState.CONVERGING_1:
                self.insert_with_pending(1, output)
                self.low -= self.bits_system.HALF
            # In case of a near-convergence, increment the pending bits counter and turn low's second MSB from 1 to 0:
            case IntervalState.NEAR_CONVERGENCE:
                self.pending_bits += 1
                self.low -= self.bits_system.ONE_FOURTH

        # In every case, Get rid of low's and width's MSB:
        self.low <<= 1
        self.width <<= 1

    def __call__(self, input_data: bytes) -> bytes:
        """
        Compresses the given input data using arithmetic coding.
        :param input_data: The data which will be compressed.
        :return: A bytes object containing the input data after compression.
        """
        # Initialize CFI dictionary:
        self.init_cum_freqs(input_data)

        # Initialize the current interval and the pending bits counter:
        self.low, self.width, self.pending_bits = 0, self.bits_system.MAX_CODE, 0

        # Initialize output buffer:
        output = BitBuffer()

        # Compress the full message, along with an EOF value, to let the decoder know when the input ends:
        for input_value in itertools.chain(input_data, (self.eof,)):
            # Update the current interval:
            self.update_interval(input_value)

            # Process special interval states and output bits accordingly:
            while (state := IntervalState.get_state(self.low, self.low + self.width, self.bits_system)) is not IntervalState.NON_CONVERGING:
                self.process_state(state, output)

        # When the loop exits, the possible boundaries are:
        # - [01yyy, 11xxx)
        # - [00yyy, 11xxx)
        # - [00yyy, 10xxx)
        # So we must insert '01' if low is '00', and '10' if low is '01'. Along with those, any pending near-convergence
        # bits must be inserted as well. A simple way of doing it is just adding 1 to the near-convergence counter and
        # insert the value of low's second MSB:
        self.pending_bits += 1
        self.insert_with_pending(self.low >> (self.bits_system.BITS_USED - 2), output)

        # The padding that BitBuffer appends to the data is ok. Since it is only zeroes, it does not change the number
        # that the compressor had produced:
        return bytes(output)
