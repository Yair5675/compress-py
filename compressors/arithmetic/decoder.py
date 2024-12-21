import util
from typing import Optional
from collections import deque
from compressors.arithmetic.ppm import PPMModelChain
from compressors.arithmetic.bits_system import BitsSystem
from compressors.arithmetic.interval_state import Interval, IntervalState
from compressors.arithmetic.arithmetic_iter import ArithmeticIterator, StateCallback


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
        '__history',

        # The statistical model chain:
        'ppm_chain',

        # The bytes currently decoded and the index of the next bit to load:
        'encoded_bytes', 'next_bit_idx'
    )

    def __init__(self, system: BitsSystem, max_ppm_order: int):
        start_interval = Interval(low=0, width=system.MAX_CODE, system=system)
        self.interval_iterator: ArithmeticIterator = ArithmeticIterator(start_interval, self)

        self.__history: deque[int] = deque()
        self.ppm_chain: PPMModelChain = PPMModelChain(max_ppm_order)

    @property
    def value(self) -> int:
        return self.__value

    @value.setter
    def value(self, value) -> None:
        # Make sure 'value' abides to the number of bits in the interval's system:
        self.__value: int = value & self.interval_iterator.current_interval.system.MAX_CODE

    @property
    def history(self) -> tuple[int]:
        return tuple(self.__history)

    def add_to_history(self, symbol: int):
        self.__history.append(symbol)
        if len(self.__history) > self.ppm_chain.max_order:
            self.__history.popleft()

    def process_interval(self, interval: Interval) -> bool:
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

    def init_value(self, compressed_bytes: bytes) -> None:
        """
        Inserts the first bits of `compressed_bytes` into `self.value`.
        :param compressed_bytes: The data the Decoder will compress. Its first bits will be loaded into the object to
                                 begin decompression.
        """
        # Initialize value:
        self.value = 0

        # Calculate how many bits we can get from the compressed data:
        system: BitsSystem = self.interval_iterator.current_interval.system
        input_bits_len = min(8 * len(compressed_bytes), system.BITS_USED)
        for i in range(input_bits_len):
            self.value = (self.value << 1) | util.get_bit(compressed_bytes, i)

        # Shift additional zeroes if needed:
        remaining = max(0, system.BITS_USED - input_bits_len)
        self.value <<= remaining

    def __call__(self, encoded_bytes: bytes) -> Optional[bytes]:
        """
        Decodes a sequence of bytes representing an encoding of data using the Encoder class.
        :param encoded_bytes: Data that was encoded using Arithmetic Coding (with the Encoder class).
        :return: The original data that was encoded using Arithmetic Coding, or None if the data wasn't encoded properly
                 and caused decoding to fail.
        """
        # Save the encoded bytes and reset the next-bit-idx:
        self.encoded_bytes, self.next_bit_idx = encoded_bytes, 0

        # Initialize the value:
        self.init_value(encoded_bytes)

        # Use a bytearray to efficiently concatenate the decoded bytes:
        decoded: bytearray = bytearray()

        # Continue to try to decode until there is an EOF symbol, and add a timeout once the next bit index has gone
        # over all the bits, plus the number of bits used by the bits system:
        timeout_idx = 8 * len(encoded_bytes) + self.interval_iterator.current_interval.system.BITS_USED
        while self.next_bit_idx < timeout_idx:
            # Get the current symbol:
            current_symbol = self.ppm_chain.get_symbol(self.value, self.interval_iterator.current_interval, self.history)
            if current_symbol is None:
                return None
            elif current_symbol == 256:  # EOF symbol, not valid bytes value
                break
            else:
                decoded.append(current_symbol)

            # Update the interval like the encoder:
            prob_interval = self.ppm_chain.get_prob_interval(current_symbol, self.history)
            self.add_to_history(current_symbol)
            self.interval_iterator.process_prob_interval(prob_interval)

        # Convert the array to bytes:
        return bytes(decoded)
