from dataclasses import dataclass
from compressors.arithmetic.frequency_table import MutableFrequencyTable


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
        self.tables: dict[Context, MutableFrequencyTable] = {}
