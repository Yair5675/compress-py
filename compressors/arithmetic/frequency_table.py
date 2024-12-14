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


class EqualFrequenciesTable(FrequencyTable):
    """
    A frequency table that assumes all byte values and the eof value appear the same number of times in the data.
    """
    def get_prob_interval(self, symbol: int) -> ProbabilityInterval:
        """
        Calculates the associated probability interval of the symbol, assuming all of them appear the same amount of
        times.
        :param symbol: A value in the range [0, 256] whose probability interval will be returned.
        :return: A probability interval representing the given symbol.
        """
        # Check range:
        if 0 > symbol or symbol > 256:
            raise ValueError(f"Invalid input value: {symbol} is neither a byte value nor an EOF value (256)")

        # Return equal probability:
        return ProbabilityInterval(low_freq=symbol, high_freq=symbol + 1, tot_freq=257)

    def get_symbol(self, value: int, interval: Interval) -> Optional[int]:
        """
        Returns the byte value (or eof value) associated with the value's location inside the interval, assuming all
        values appear the same number of times in the data.
        """
        # Calculate cumulative frequency:
        cum_freq = (((value - interval.low + 1) * 257) - 1) // interval.width

        # If the cumulative frequency is not within the range [0, 256], return None:
        if 0 > cum_freq or cum_freq > 256:
            return None

        # Since every symbol is assumed to have a frequency of 1, the cumulative frequency IS the symbol:
        return cum_freq
