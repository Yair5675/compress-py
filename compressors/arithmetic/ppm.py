from collections import defaultdict
from collections.abc import Sequence
from compressors.arithmetic.frequency_table import *
from compressors.arithmetic.interval_state import Interval


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


class PPMModelChain:
    """
    Main PPM model class, contains multiple PPM models with different orders to provide probability intervals
    considering the symbols' contexts.
    """
    __slots__ = (
        # The maximum model order in the chain, will determine the space usage by the program (generally it is O(257^n),
        # so let's keep it low ok?):
        '__max_order',

        # The constant, -1 context, model we fall back on in case all mutable models fail us:
        '__fallback_model',

        # The tuple containing the models:
        '__models'
    )

    def __init__(self, max_order: int) -> 'PPMModelChain':
        # Set max order once and for all (also validate):
        if max_order < 0:
            raise ValueError("Maximum model order mustn't be negative")
        self.__max_order: int = max_order

        # Initialize fallback model:
        self.__fallback_model: EqualFrequenciesTable = EqualFrequenciesTable()

        # Initialize mutable models according to max_order:
        self.__models: tuple[PPMModel] = tuple(PPMModel(i) for i in range(max_order + 1))

    @property
    def max_order(self) -> int:
        return self.__max_order

    def get_prob_interval(self, symbol: int, history: Sequence[int]) -> ProbabilityInterval:
        """
        Given a symbol and its history (previous symbols), the method returns the probability interval assigned with
        the symbol and the most amount of previous symbols (i.e: the longest context).
        The maximum length of the context that will be taken into account will be `max_order`, and if the sequence is
        longer than `max_order`, only the last `max_order` elements will be taken into account.

        Note that this method also updates the models saved in the object, so calling this method with the same
        arguments will almost definitely NOT provide the same results.
        :param symbol: The symbol whose probability interval will be returned.
        :param history: Symbols that occurred before the current one, and will be used to better predict the probability
                        interval of the current symbol. Note that if history contains more symbols than the maximum
                        order of the model chain, not all of them will be considered.
        :return: The probability interval currently associated with the symbol, given this history.
        """
        # Go from the highest order possible to the lowest:
        for model_order in range(min(self.max_order, len(history)), -1, -1):
            # Create the context:
            current_context: Context = Context(history[-model_order:]) if model_order != 0 else Context(())

            # Try to get the probability interval:
            current_model: PPMModel = self.__models[model_order]
            prob_interval: ProbabilityInterval = current_model.get_prob_interval(symbol, current_context)

            # Update the current model using this context. Note that if we found the probability interval in a model,
            # we only need to update it and models with higher order. Models with lower order won't be updated:
            current_model.update_model(symbol, current_context)

            # If the interval is not None, return it and break out of the loop. If it is, continue to the next model:
            if prob_interval is not None:
                return prob_interval

        # If all models were searched, updated and didn't find a probability interval, use the fallback model:
        return self.__fallback_model.get_prob_interval(symbol)

    def get_symbol(self, value: int, current_interval: Interval, history: Sequence[int]) -> Optional[int]:
        """
        Given the current interval in the decoding process, and a value inside that interval, the method returns the
        symbol associated with the value's location inside the interval.
        The method will try to calculate the symbol starting with the highest-order model and ending with order 0 model.
        If all models fail to calculate the symbol, the fallback frequency table will provide it.
        :param value: A value inside the current interval, whose location inside it will determine the symbol returned.
                      Note that the data inside `value` should match the bits system saved inside `current_interval`.
        :param current_interval: The current interval in the decoding process.
        :param history: Symbols that occurred before the current one. They will allow the method to pick the exact
                        symbol encoded during compression by choosing the right models and frequency tables. Note that
                        if history contains more symbols than the maximum order of the model chain, not all of them will
                        be considered.
        :return: The symbol that matched the location of `value` inside `current_interval`. If the combinations of
                 `value` and `current_interval` are nonsensical (produce an invalid cumulative frequency value in all
                 models), None will be returned.
        """
        # Go from the highest order possible to the lowest:
        for model_order in range(min(self.max_order, len(history)), -1, -1):
            # Create the context:
            current_context: Context = Context(history[-model_order:]) if model_order != 0 else Context(())

            # Calculate cumulative frequency for this model:
            current_table: MutableFrequencyTable = self.__models[model_order].tables[current_context]
            cum_freq: int = PPMModelChain.__calc_cum_freq(value, current_interval, current_table)

            # If the cumulative frequency is between 0 and the model's total frequencies value, calculate and return
            # the symbol:
            if 0 <= cum_freq < current_table.get_total_frequencies():
                return current_table.get_symbol(cum_freq)

        # If all models were searched and didn't find a symbol, try the fallback model:
        return self.__fallback_model.get_symbol(
            PPMModelChain.__calc_cum_freq(value, current_interval, self.__fallback_model)
        )

    @staticmethod
    def __calc_cum_freq(value: int, interval: Interval, table: FrequencyTable) -> int:
        """
        A helper method that calculates cumulative frequency from a value and its position in an interval, while using
        a frequency table.
        """
        return (((value - interval.low + 1) * table.get_total_frequencies()) - 1) // interval.width
