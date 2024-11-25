from collections import defaultdict
from compressors.arithmetic.bits_system import BitsSystem


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
