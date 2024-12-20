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

    def insert_with_pending(self, bit: int) -> None:
        """
        Inserts the given bit to the output buffer saved in the object, along with 'n' additional bits holding the
        inversion of the given bit, where 'n' is the 'pending_bits' attribute in the object.
        The method set 'pending_bits' to 0 at the end of this method.
        :param bit: A bit that will be inserted to the output buffer, along with repetitions of its inversion. Must be
                    1 or 0.
        """
        # Insert the bit:
        self.output_buffer.insert_bits(bit, 1)

        # Insert pending bits in groups of 32:
        bits_to_insert = 0 if bit else 0xFFFFFFFF
        for _ in range(self.pending_bits // 32):
            self.output_buffer.insert_bits(bits_to_insert, 32)
        if self.pending_bits % 32 > 0:
            self.output_buffer.insert_bits(bits_to_insert, self.pending_bits % 32)

        # Clear the pending bits:
        self.pending_bits = 0

    def process_interval(self, interval: Interval) -> bool:
        match interval.get_state():
            # If the interval is non-converging, do nothing and signal to stop calling the callback:
            case IntervalState.NON_CONVERGING:
                return False

            # In case of a matching MSB, output it and make sure `interval.low` is less than half:
            case IntervalState.CONVERGING_0:
                self.insert_with_pending(bit=0)
            case IntervalState.CONVERGING_1:
                self.insert_with_pending(bit=1)
                interval.low -= interval.system.HALF

            # In case of a near-convergence, increment the pending bits counter and turn the second MSB of the
            # interval's 'low' value from 1 to 0 (by subtracting a fourth):
            case IntervalState.NEAR_CONVERGENCE:
                self.pending_bits += 1
                interval.low -= interval.system.ONE_FOURTH

        # In every case, Get rid of low's and width's MSB:
        interval.low <<= 1
        interval.width <<= 1

        # Since we changed the interval, return True to call the callback again:
        return True

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
