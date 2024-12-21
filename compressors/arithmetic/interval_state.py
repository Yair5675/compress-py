from enum import Enum, auto
from compressors.arithmetic import bits_system


class Interval:
    """
    A class representing an encoding/decoding interval.
    """
    __slots__ = (
        # Starting point of the interval, between 0 and 1:
        '__low',
        # The width of the interval, between 0 and 1:
        '__width',
        # The bits system used in the `low` and `width` values:
        'system'
    )

    def __init__(self, low: int, width: int, system: bits_system.BitsSystem) -> 'Interval':
        self.system: bits_system.BitsSystem = system
        self.low: int = low
        self.width: int = width

    @property
    def low(self) -> int:
        return self.__low

    @low.setter
    def low(self, value) -> None:
        self.__low: int = value & self.system.MAX_CODE

    @property
    def width(self) -> int:
        return self.__width

    @width.setter
    def width(self, value):
        self.__width: int = value & self.system.MAX_CODE

    @property
    def high(self):
        return self.low + self.width

    def update(self, probability_interval) -> None:
        """
        Given a probability interval representing some section inside the current interval object, the method transforms
        the interval object into this subsection.
        :param probability_interval: A ProbabilityInterval object representing a subsection in the current interval.
        """
        # Update low and width:
        self.low += self.width * probability_interval.low_freq // probability_interval.tot_freq
        self.width = (self.width * probability_interval.high_freq // probability_interval.tot_freq -
                      self.width * probability_interval.low_freq // probability_interval.tot_freq)

    def get_state(self) -> 'IntervalState':
        """
        Returns the state of the current interval, represented as the IntervalState enum.
        :return: An IntervalState variant describing the state of the current interval.
        """
        # Check convergence:
        if self.low >= self.system.HALF:
            return IntervalState.CONVERGING_1
        elif self.high < self.system.HALF:
            return IntervalState.CONVERGING_0
        # Check near-convergence:
        elif self.low >= self.system.ONE_FOURTH and self.high < self.system.THREE_FOURTHS:
            return IntervalState.NEAR_CONVERGENCE
        # Default - non-converging:
        else:
            return IntervalState.NON_CONVERGING


class IntervalState(Enum):
    """
    During compression/decompression, the interval boundaries 'low' and 'high' determine the output. Their state
    determines the outputted bit. This enum contains every state those boundaries can be in:
    """
    # Both low and high's MSB is 0:
    CONVERGING_0 = auto()

    # Both low and high's MSB is 1:
    CONVERGING_1 = auto()

    # Near-convergence (low >= one fourth, and high < three fourths):
    NEAR_CONVERGENCE = auto()

    # Not converging (none of the above):
    NON_CONVERGING = auto()

    def is_converging(self) -> bool:
        """
        Checks whether the current interval state is CONVERGING_0 or CONVERGING_1.
        :return: True if self is a converging variant of IntervalState, false otherwise.
        """
        return self is IntervalState.CONVERGING_0 or self is IntervalState.CONVERGING_1

    @staticmethod
    def get_state(low: int, high: int, system: bits_system.BitsSystem) -> 'IntervalState':
        # Check convergence:
        if low >= system.HALF:
            return IntervalState.CONVERGING_1
        elif high < system.HALF:
            return IntervalState.CONVERGING_0
        # Check near-convergence:
        elif low >= system.ONE_FOURTH and high < system.THREE_FOURTHS:
            return IntervalState.NEAR_CONVERGENCE
        # Default - non-converging:
        else:
            return IntervalState.NON_CONVERGING
