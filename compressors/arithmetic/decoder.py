from compressors.arithmetic.bits_system import BitsSystem


class Decoder:
    __slots__ = (
        # Current interval's starting value and length:
        '__low', '__width',

        # The current piece of the compressed data held and processed:
        '__value',

        # An index to the next bit in the compressed data that will be read:
        'bit_offset',

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
