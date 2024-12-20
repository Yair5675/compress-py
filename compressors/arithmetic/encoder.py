from collections import deque
from util.bitbuffer import BitBuffer
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.bits_system import BitsSystem
from compressors.arithmetic.frequency_table import ProbabilityInterval
from compressors.arithmetic.interval_state import Interval, IntervalState
from compressors.arithmetic.arithmetic_iter import StateCallback, ArithmeticIterator


class Encoder(StateCallback):
    """
    A class performing the encoding phase of arithmetic coding.
    """

    __slots__ = (
        # The number of pending bits from near-convergence situations during encoding:
        'pending_bits',

        # The interval iterator object:
        'interval_iterator',

        # History of previous symbols encoded (for the statistical model). Its max length is the max order of the ppm
        # model chain:
        'history',

        # The statistical model chain used during encoding:
        'ppm_chain',

        # Output buffer that holds the encoded part:
        'output_buffer'
    )

    def __init__(self, system: BitsSystem, max_ppm_order: int) -> 'Encoder':
        self.pending_bits: int = 0

        start_interval = Interval(0, system.MAX_CODE, system)
        self.interval_iterator: ArithmeticIterator = ArithmeticIterator(start_interval, self)

        self.history: deque[int] = deque()
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

    def add_to_history(self, value: int) -> None:
        """
        Adds a value to the history of the encoding, and shortens that history if the new length is larger than the max
        order of the ppm model chain.
        :param value: A byte value or EOF value that was previously encoded.
        """
        self.history.append(value)
        if len(self.history) > self.ppm_chain.max_order:
            self.history.popleft()

    def __call__(self, value: int) -> None:
        """
        Encodes the given value and saves the result in the object.
        :param value: A value that will be encoded using arithmetic coding. The value must be in the range [0, 256],
                      where [0, 256) represents all byte values, and 256 represents EOF.
        """
        # Get the probability interval of the value and update the PPM model chain:
        prob_interval: ProbabilityInterval = self.ppm_chain.get_prob_interval(value, tuple(self.history))
        self.add_to_history(value)

        # Use the iterator with this interval:
        self.interval_iterator.process_prob_interval(prob_interval)

    def get_encoded(self) -> bytes:
        """
        Returns the bytes of the encoded values inside the encoder.
        :return: The bytes representing the encoding of all values provided to the Encoder.
        """
        # When the encoding is finished, the possible interval boundaries are:
        # - [01yyy, 11xxx)
        # - [00yyy, 11xxx)
        # - [00yyy, 10xxx)
        # So we must insert '01' if low is '00', and '10' if low is '01'. Along with those, any pending near-convergence
        # bits must be inserted as well. A simple way of doing it is just adding 1 to the near-convergence counter and
        # insert the value of low's second MSB:
        self.pending_bits += 1
        interval = self.interval_iterator.current_interval
        self.insert_with_pending(interval.low >> (interval.system.BITS_USED - 2))

        # Once we inserted those, just convert the BitBuffer to bytes (padding added due to it doesn't affect us,
        # because adding zeroes to the number's end doesn't change its value):
        return bytes(self.output_buffer)
