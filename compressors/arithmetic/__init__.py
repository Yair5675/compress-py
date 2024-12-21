import util
from typing import Optional
from collections import deque
from compressors import Compressor
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.bits_system import BitsSystem
from compressors.arithmetic.interval_state import Interval, IntervalState
from compressors.arithmetic.arithmetic_iter import StateCallback, ArithmeticIterator


class Decoder(StateCallback):
    """
    A class performing the encoding phase of arithmetic coding.
    """
    __slots__ = (
        # The value we form from the input. Its location inside the interval in 'interval_iterator' will tell us the
        # next symbol in the decoding process:
        '__value',

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

    @property
    def value(self) -> int:
        return self.__value

    @value.setter
    def value(self, value) -> None:
        # Make sure 'value' abides to the number of bits in the interval's system:
        self.__value: int = value & self.interval_iterator.current_interval.system.MAX_CODE

    def process_interval(self, interval: interval_state.Interval) -> bool:
        match interval.get_state():
            # Signal the caller to stop calling this callback if the interval is non-converging:
            case IntervalState.NON_CONVERGING:
                return False

            # In the case of CONVERGING_0, do nothing for now. If it's CONVERGING_1, clear the MSB of value:
            case IntervalState.CONVERGING_1:
                interval.low -= interval.system.HALF  # TODO: This line seems to have no effect, as the MSB of low is shifted out later. Find out if it's necessary
                self.value -= interval.system.HALF

            # If we are dealing with near-convergence, clear the second MSB in low and value:
            case IntervalState.NEAR_CONVERGENCE:
                interval.low -= interval.system.ONE_FOURTH
                self.value -= interval.system.ONE_FOURTH

        # Clear the MSBs of value, low and width:
        interval.low <<= 1
        interval.width <<= 1
        self.value <<= 1

        # Insert a new bit from the input to value (insert 0 if we ran out of bits):
        input_bits_count = 8 * len(self.encoded_bytes)
        next_bit = util.get_bit(self.encoded_bytes, self.next_bit_idx) if self.next_bit_idx < input_bits_count else 0
        self.value |= next_bit
        self.next_bit_idx += 1

        # Signal the caller to call the callback again on the new interval:
        return True

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
