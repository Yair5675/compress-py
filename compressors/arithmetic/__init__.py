from typing import Optional
from collections import deque
from compressors import Compressor
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.bits_system import BitsSystem
from compressors.arithmetic.interval_state import Interval
from compressors.arithmetic.arithmetic_iter import StateCallback, ArithmeticIterator


class Decoder(StateCallback):
    """
    A class performing the encoding phase of arithmetic coding.
    """
    __slots__ = (
        # The value we form from the input. Its location inside the interval in 'interval_iterator' will tell us the
        # next symbol in the decoding process:
        'value',

        # The interval iterator object:
        'interval_iterator',

        # History of previous symbols decoded (for the statistical model). Its max length is the max order of the ppm
        # model chain:
        'history',

        # The statistical model chain:
        'ppm_chain',

        # The bytes currently decoded and the index of the next bit to load:
        'encoded_bytes', 'next_bit_idx'
    )

    def __init__(self, system: BitsSystem, max_ppm_order: int):
        start_interval = Interval(low=0, width=system.MAX_CODE, system=system)
        self.interval_iterator: ArithmeticIterator = ArithmeticIterator(start_interval, self)

        self.history: deque[int] = deque()
        self.ppm_chain: PPMModelChain = PPMModelChain(max_ppm_order)

    def process_interval(self, interval: interval_state.Interval) -> bool:
        # TODO
        pass

    def __call__(self, encoded_bytes: bytes) -> Optional[bytes]:
        """
        Decodes a sequence of bytes representing an encoding of data using the Encoder class.
        :param encoded_bytes: Data that was encoded using Arithmetic Coding (with the Encoder class).
        :return: The original data that was encoded using Arithmetic Coding, or None if the data wasn't encoded properly
                 and caused decoding to fail.
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
