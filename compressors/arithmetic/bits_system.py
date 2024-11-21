from dataclasses import dataclass


@dataclass(init=False)
class BitsSystem:
    """
    Arithmetic coding deals with precision problems since we unfortunately can't have infinite bits. Therefor, the
    program needs to know how many bits should be used for calculations. This class saves those values and allows
    them to be easily configured.
    """
    # Number of bits used in the system:
    BITS_USED: int

    # Maximum value that can be saved in the current bit system:
    MAX_CODE: int

    # Half - the value used when testing convergence:
    HALF: int

    # One fourth and three fourths - values used when testing near-convergence:
    ONE_FOURTH: int
    THREE_FOURTHS: int

    def __init__(self, max_bits_used: int) -> 'BitsSystem':
        """
        Generates the bit system values necessary, according to the number of bits the maximum value should hold.
        :param max_bits_used: The maximum number of bits a value can hold in the created bit system.
        """
        # Save the max_bits_used:
        self.BITS_USED = max_bits_used

        # Get the max code value in the system (all ones, `max_bits_used` times):
        self.MAX_CODE = 0
        for _ in range(max_bits_used):
            self.MAX_CODE = (self.MAX_CODE << 1) | 1

        # Define half as a 1 bit followed by all zeroes:
        self.HALF = 1 << (max_bits_used - 1)

        # Define one fourth as '01' bits, followed by all zeroes:
        self.ONE_FOURTH = self.HALF >> 1

        # Define three fourths as '11' bits, followed by all zeroes:
        self.THREE_FOURTHS = self.HALF | self.ONE_FOURTH


class InsufficientValueRange(Exception):
    """
    Represents a situation were a chosen bit system is too small to represent all needed values uniquely
    """
    def __init__(self, values_to_represent: int):
        msg: str = f"Chosen bit system isn't sufficient to uniquely represent {values_to_represent} values"
        super().__init__(msg)