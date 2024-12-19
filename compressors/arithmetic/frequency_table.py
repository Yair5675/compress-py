from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from compressors.arithmetic.fenwick import FenwickTree


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
    def get_symbol(self, cumulative_frequency: int) -> Optional[int]:
        """
        Given a cumulative frequency value, the table returns the symbol whose probability interval contains this value.
        If no symbol's interval contains the cumulative frequency, None is returned.
        :param cumulative_frequency: A cumulative frequency value that lies inside some symbol's interval. The method
                                     will find and return this symbol.
        :return: The byte value (or EOF value) associated with the cumulative frequency, or None if a matching interval
                 is not found.
        """
        pass

    @abstractmethod
    def get_total_frequencies(self) -> int:
        """
        Calculates the sum of all frequencies saved in the table (i.e: the `high` value for the last symbol's
        probability interval).
        :return: The sum of all frequencies in the table.
        """
        pass


class EqualFrequenciesTable(FrequencyTable):
    """
    A frequency table that assumes all byte values and the eof value appear the same number of times in the data.
    """

    def get_total_frequencies(self) -> int:
        # If there are 257 symbols, and each is assumed to have a frequency of one, then the total is:
        return 257

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

    def get_symbol(self, cumulative_frequency: int) -> Optional[int]:
        """
        Returns the byte value (or eof value) associated with the cumulative frequency, assuming all symbols appear the
        same number of times in the data.
        """
        # If the cumulative frequency is not within the range [0, 256], return None:
        if 0 > cumulative_frequency or cumulative_frequency > 256:
            return None

        # Since every symbol is assumed to have a frequency of 1, the cumulative frequency IS the symbol:
        return cumulative_frequency




class MutableFrequencyTable(FrequencyTable):
    """
    A frequency table that allows users to change and update the frequencies of a given value.
    """

    __slots__ = (
        # Total cumulative frequencies saved in the table (converts O(log n) to O(1) when calculating it):
        'tot_freqs',

        # The fenwick tree holding the frequencies, allows us to efficiently calculate and update cumulative
        # frequencies:
        'frequencies'
    )

    def __init__(self):
        """
        Initializes an empty MutableFrequencyTable.
        """
        # Initialize a fenwick tree that holds 258 zeroes (256 byte values + an EOF value, and remember each index's
        # interval is defined by the current AND next index, so we add 1 element at the end):
        self.frequencies: FenwickTree = FenwickTree([0] * 258)
        self.tot_freqs: int = 0

    def get_prob_interval(self, symbol: int) -> ProbabilityInterval:
        # Check range:
        if 0 > symbol or symbol > 256:
            raise ValueError(f"Invalid input value: {symbol} is neither a byte value nor an EOF value (256)")

        # Calculate cumulative frequencies for both `low` and `high`:
        low_cum, high_cum = self.frequencies.get_sum(symbol), self.frequencies.get_sum(symbol + 1)
        return ProbabilityInterval(low_cum, high_cum, self.tot_freqs)

    def get_symbol(self, cumulative_frequency: int) -> Optional[int]:
        # Perform binary search in combination with fenwick tree to find the corresponding symbol in O(log^2(n)):
        def binary_search(left: int, right: int):
            if left > right:
                return None

            middle = (left + right) // 2
            low_cum, high_cum = self.frequencies.get_sum(middle), self.frequencies.get_sum(middle + 1)
            if low_cum > cumulative_frequency:
                return binary_search(left, middle - 1)
            elif high_cum <= cumulative_frequency:
                return binary_search(middle + 1, right)
            else:
                return middle

        # The binary search returns None if the cumulative frequency is not within the saved range, so just return its
        # result:
        return binary_search(0, 257)

    def increment_symbol(self, symbol: int, amount: int = 1) -> None:
        """
        Increments the frequency of the given symbol by some amount.
        :param symbol: The symbol whose frequency will be incremented, must be in the range [0, 256].
        :param amount: The amount that will be added to the current frequency of `symbol`.
        """
        # Check range:
        if 0 > symbol or symbol > 256:
            raise ValueError(f"Invalid input value: {symbol} is neither a byte value nor an EOF value (256)")

        # Check amount:
        if amount < 0:
            raise ValueError("Negative increment is not allowed")

        # Use our beloved fenwick tree:
        self.frequencies.add(symbol, amount)
        self.tot_freqs += amount

    def get_total_frequencies(self) -> int:
        # We already save it to provide O(1) calculation:
        return self.tot_freqs
