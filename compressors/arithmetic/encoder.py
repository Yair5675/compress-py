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

        # A dictionary mapping between an input value (byte value or EOF) and its cumulative frequency interval:
        'cum_freqs'
    )

    def __init__(self, eof: int, bits_system: BitsSystem) -> 'Encoder':
        self.bits_system = bits_system
        self.eof = eof
        self.cum_freqs: dict[int, tuple[int, int]]

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
