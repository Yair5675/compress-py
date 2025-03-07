#     Compress-py  A command-line interface for compressing files
#     Copyright (C) 2025  Yair Ziv
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from enum import Enum, auto
from compressors.arithmetic import bits_system


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
