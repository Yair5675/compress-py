from abc import ABC, abstractmethod
from compressors.arithmetic import interval_state


class StateCallback(ABC):
    """
    A callback used for handling IntervalState variants (not including NON_CONVERGING).
    """

    @abstractmethod
    def process_state(self, interval: interval_state.Interval, state: interval_state.IntervalState) -> bool:
        """
        Depending on an interval and its state, the method will perform different actions.
        Note that the interval given as parameter should be treated as mutable, and may change after the method call.

        After the method is executed, it returns a boolean. If true - the method's caller should re-compute the
        interval's state and call the method again (it indicates the interval was mutated). If false - do not call it
        again right after the method is finished.
        :param interval: The interval that the state belongs to. It should be treated as mutable.
        :param state: The state of the interval, will help decide what actions to take.
        :return: True if the interval was mutated and the method should be called on it (and its new state) again, False
                 otherwise.
        """
        pass


class ArithmeticIterator:
    """
    A class that iterates over intervals during both compression and decompression. Handling the interval's state is
    customizable through a callback.
    """

    __slots__ = (
        # The current interval, basically the object's state:
        'current_interval',

        # The callback that will be used to process the current interval's state:
        'state_callback'
    )

    def __init__(self, start_interval: interval_state.Interval, state_callback: StateCallback) -> 'ArithmeticIterator':
        self.current_interval: interval_state.Interval = start_interval
        self.state_callback: StateCallback = state_callback
