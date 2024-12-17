from typing import Optional
from dataclasses import dataclass
from collections import defaultdict
from compressors.arithmetic.frequency_table import MutableFrequencyTable, ProbabilityInterval


@dataclass(frozen=True)
class Context:
    """
    A helper dataclass holding the last 'n' byte values before the currently read value.
    """
    history: tuple[int]

    def __len__(self):
        return len(self.history)


class PPMModel:
    __slots__ = (
        # The order of the current model, i.e: number of previous values taken into account when calculating the
        # probabilities for the current one:
        'order',

        # A mapping between different contexts and frequency tables. Note that the amount of frequency tables needed
        # grows exponentially as the order grows linearly:
        'tables'
    )

    def __init__(self, order: int) -> 'PPMModel':
        self.order: int = order

        # Implement tables as a defaultdict that creates frequency tables if necessary:
        self.tables: defaultdict[Context, MutableFrequencyTable] = defaultdict(MutableFrequencyTable)

    def get_prob_interval(self, symbol: int, context: Context) -> Optional[ProbabilityInterval]:
        """
        Given a symbol and its context, the model returns the probability interval assigned to that symbol-context pair.
        Note that the length of the context HAS to match the order of the model (no more and no less).
        :param symbol: The symbol whose probability interval will be returned.
        :param context: The sequence of symbols that appeared before the current symbol. The length of this context
                        must match the order of the model EXACTLY (i.e: If the model's order is 3, context will contain
                        three symbols).
        :return: If the symbol, considering the given context, isn't associated with any probability interval, None is
                 returned. Otherwise, this associated probability interval is returned.
        """
        # Check history length:
        if self.order != len(context):
            raise ValueError(f"History length must equal the model's order")

        # Get the frequency table corresponding to that context:
        freq_table: MutableFrequencyTable = self.tables[context]

        # Get the probability interval, and return it only if it doesn't represent zero probability:
        prob_interval: ProbabilityInterval = freq_table.get_prob_interval(symbol)
        return prob_interval if prob_interval.low_freq != prob_interval.high_freq else None

    def update_model(self, symbol: int, context: Context) -> None:
        """
        Updates the model according to the appeared symbol and the context leading up to it.
        This will effectively enlarge the probability assigned to 'symbol' given this context.
        Note that the context's length MUST equal the model's order (no more, no less).
        :param symbol: The current symbol. Its probability interval will increase (in this particular context).
        :param context: The sequence of symbols before the given one. The number of symbols in this context must equal
                        the model's order.
        """
        # Check context length:
        if self.order != len(context):
            raise ValueError(f"Context length must equal the model's order")

        # Get the frequency table assigned with the context:
        freq_table: MutableFrequencyTable = self.tables[context]

        # Update symbol:
        freq_table.increment_symbol(symbol)
