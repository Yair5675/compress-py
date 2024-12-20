from compressors import Compressor
from util.bitbuffer import BitBuffer
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.interval_state import IntervalState, Interval
from compressors.arithmetic.bits_system import BitsSystem, InsufficientValueRange
from compressors.arithmetic.arithmetic_iter import ArithmeticIterator, StateCallback


class Encoder(StateCallback):
    """
    A class performing the encoding phase of arithmetic coding.
    """

    __slots__ = (
        # The number of pending bits from near-convergence situations during encoding:
        'pending_bits',

        # The interval iterator object:
        'interval_iterator',

        # The statistical model chain used during encoding:
        'ppm_chain',

        # Output buffer that holds the encoded part:
        'output_buffer'
    )

    def __init__(self, system: BitsSystem, max_ppm_order: int) -> 'Encoder':
        self.pending_bits: int = 0

        start_interval = Interval(0, system.MAX_CODE, system)
        self.interval_iterator: ArithmeticIterator = ArithmeticIterator(start_interval, self)

        self.ppm_chain: PPMModelChain = PPMModelChain(max_ppm_order)

        self.output_buffer: BitBuffer = BitBuffer()

    def process_interval(self, interval: Interval) -> bool:
        # TODO
        pass

    def __call__(self, value: int) -> None:
        """
        Encodes the given value and saves the result in the object.
        :param value: A value that will be encoded using arithmetic coding. The value must be in the range [0, 256],
                      where [0, 256) represents all byte values, and 256 represents EOF.
        """
        # TODO
        pass

    def get_encoded(self) -> bytes:
        """
        Returns the bytes of the encoded values inside the encoder.
        :return: The bytes representing the encoding of all values provided to the Encoder.
        """
        # TODO
        pass


class ArithmeticCompressor(Compressor):
    __slots__ = (
        # The bits system used in encoding/decoding:
        'bits_system',
    )

    def __init__(self, system: BitsSystem) -> 'ArithmeticCompressor':
        self.bits_system = system

    def encode(self, input_data: bytes) -> bytes:
        # TODO: Compress using the Encoder class
        pass

    def decode(self, compressed_data: bytes) -> bytes:
        # TODO: Decompress using the Decoder class
        pass
