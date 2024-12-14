from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from compressors.arithmetic.interval_state import Interval


@dataclass(frozen=True)
class ProbabilityInterval:
    # Cumulative frequency up to the current interval:
    low_freq: int

    # Cumulative frequency up to and including the current interval:
    high_freq: int

    # Total cumulative frequency:
    tot_freq: int


class FrequencyTable(ABC):
    """
    An interface describing the necessary methods for any frequency table.
    """
    @abstractmethod
    def get_prob_interval(self, symbol: int) -> ProbabilityInterval:
        """
        Given a value in the range [0, 256], the frequency table returns the probability interval associated with this
        value.
        :param symbol: An integer in the range [0, 256], where [0, 256) represent all possible byte values, and 256
                       represents the EOF value.
        :return: The probability interval associated with `symbol`.
        """
        pass

    @abstractmethod
    def get_symbol(self, value: int, interval: Interval) -> Optional[int]:
        """
        Given an interval and a value inside that interval, the method returns the symbol associated with the location
        of the value inside the interval.
        :param value: A fractional value represented as an integer using a bits system. This value's bits system must
                      be the same as the system saved inside the given interval object, otherwise unexpected results
                      may arise.
        :param interval: The interval used in arithmetic encoding. It represents the range of possibilities for `value`,
                         and determines the bits system used by both of them.
        :return: The byte value (or EOF value) associated with the value's location inside the interval, or None if the
                 value-interval combinations make no sense.
        """
        pass
