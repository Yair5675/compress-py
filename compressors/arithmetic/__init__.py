from compressors import Compressor
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.frequency_table import ProbabilityInterval
from compressors.arithmetic.interval_state import IntervalState, Interval
from compressors.arithmetic.bits_system import BitsSystem, InsufficientValueRange
from compressors.arithmetic.arithmetic_iter import ArithmeticIterator, StateCallback


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
