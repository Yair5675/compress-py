import util
from util.bitbuffer import BitBuffer
from compressors.arithmetic import IntervalState
from compressors.arithmetic.bits_system import BitsSystem


class Decoder:
    __slots__ = (
        # Current interval's starting value and length:
        '__low', '__width',

        # The current piece of the compressed data held and processed:
        '__value',

        # The index pointing to the next bit that will be read from the compressed data:
        'next_bit_offset',

        # Bits system used when holding/calculating values:
        'bits_system',

        # Special EOF symbol (mustn't be a valid byte value):
        'eof',

        # Cumulative Frequency Intervals - a mapping between an input value and its interval inside the total cumulative
        # frequency of the input:
        'cfis',

        # Total frequency of the input data:
        'total_freq'
    )

    def __init__(self, bits_system: BitsSystem, eof: int, cfis: dict[int, tuple[int, int]], total_freq: int) -> 'Decoder':
        self.bits_system = bits_system
        self.eof = eof
        self.cfis = cfis
        self.total_freq = total_freq

    @property
    def low(self):
        return self.__low

    @low.setter
    def low(self, value):
        self.__low = value & self.bits_system.MAX_CODE

    @property
    def high(self):
        return self.low + self.width

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, value):
        self.__width = value & self.bits_system.MAX_CODE

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value & self.bits_system.MAX_CODE

    def init_value(self, compressed_bytes: bytes) -> None:
        """
        Inserts the first bits of `compressed_bytes` into `self.value`.
        :param compressed_bytes: The data the Decoder will compress. Its first bits will be loaded into the object to
                                 begin decompression.
        """
        # Initialize value:
        self.value = 0

        # Calculate how many bits we can get from the compressed data:
        input_bits_len = min(8 * len(compressed_bytes), self.bits_system.BITS_USED)
        for i in range(input_bits_len):
            self.value = (self.value << 1) | util.get_bit(compressed_bytes, i)

        # Shift additional zeroes if needed:
        remaining = max(0, self.bits_system.BITS_USED - input_bits_len)
        self.value <<= remaining

    def calc_cum_freq(self) -> int:
        """
        Calculates the cumulative frequency currently saved in `self.value` and returns it.
        :return: The cumulative frequency currently saved in `self.value`.
        """
        return (((self.value - self.low + 1) * self.total_freq) - 1) // self.width

    def get_byte_from_cum(self, cum_freq: int) -> int:
        """
        Given a cumulative frequency, the method returns the byte value (or EOF) whose cumulative frequency interval
        contains the given cumulative frequency.
        :param cum_freq: A cumulative frequency value.
        :return: The byte value (or EOF) that owns a CFI which contains `cum_freq`.
        """
        for byte_val, cfi in self.cfis.items():
            if cfi[0] <= cum_freq < cfi[1]:
                return byte_val
        raise ValueError(f"{cum_freq} is not a valid cumulative frequency value")

    def update_interval(self, input_value: int) -> None:
        """
        Updates the 'low' and 'width' attributes of the object based on the input value.
        This essentially updates the currently saved interval to match the input value.
        :param input_value: A byte value or EOF value whose CFI will determine the next interval.
        """
        # Get the CFI of the input value:
        cum_interval = self.cfis[input_value]

        # Update low and width:
        self.low += self.width * cum_interval[0] // self.total_freq
        self.width = self.width * cum_interval[1] // self.total_freq - self.width * cum_interval[0] // self.total_freq

    def process_state(self, compressed_data: bytes, interval_state: IntervalState) -> None:
        """
        Changes the current interval and the current part of the compressed data held according to the provided interval
        state.
        The method assumes `interval_state` is not IntervalState.NON_CONVERGING.
        :param compressed_data: The data which will be compressed. Bits from it will be read when processing the state.
        :param interval_state: The state according to which the current interval and `self.value` will change.
                               Cannot be IntervalState.NON_CONVERGING.
        """
        match interval_state:
            # In the case of CONVERGING_0, do nothing for now.
            case IntervalState.CONVERGING_1:
                # Clear leftmost bit:
                self.low -= self.bits_system.HALF
                self.value -= self.bits_system.HALF
            case IntervalState.NEAR_CONVERGENCE:
                # Clear second MSB:
                self.low -= self.bits_system.ONE_FOURTH
                self.value -= self.bits_system.ONE_FOURTH
        # Get rid of the MSB:
        self.low <<= 1
        self.width <<= 1

        # Insert another bit of the input to value:
        compressed_bits_count = 8 * len(compressed_data)
        next_bit = util.get_bit(compressed_data, self.next_bit_offset) if self.next_bit_offset < compressed_bits_count else 0
        self.next_bit_offset += 1

        self.value = (self.value << 1) | next_bit

    def __call__(self, compressed_data: bytes) -> bytes:
        """
        Decompresses the data using arithmetic coding and the provided CFIs dictionary.
        :param compressed_data: Data that was compressed using arithmetic coding, and the provided CFIs dictionary.
        :return: The original data, prior to being compressed.
        """
        # Initialize interval:
        self.low, self.width = 0, self.bits_system.MAX_CODE

        # Initialize the input value, and set the next bit offset to the amount of bits that were read:
        self.init_value(compressed_data)
        self.next_bit_offset = self.bits_system.BITS_USED

        # Initialize the output buffer:
        output = BitBuffer()

        # Continue as long as we don't encounter EOF:
        # TODO: Add some sort of timeout in case bad data was given
        while True:
            # Calculate the cumulative frequency of self.value:
            cum_freq: int = self.calc_cum_freq()

            # Get the byte value corresponding to that value, and break if it's EOF:
            org_val = self.get_byte_from_cum(cum_freq)
            if org_val == self.eof:
                break
            else:
                output.insert_bits(org_val, 8)

            # Now update the interval and process its state:
            self.update_interval(org_val)

            while (state := IntervalState.get_state(self.low, self.high, self.bits_system)) is not IntervalState.NON_CONVERGING:
                self.process_state(compressed_data, state)

        return bytes(output)

