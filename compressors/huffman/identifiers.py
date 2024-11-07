from typing import Optional
from .tree import HuffmanTree
from util.bitbuffer import BitBuffer
from functools import singledispatch


@singledispatch
def get_identifiers(_) -> dict[bytes, bytes]:
    pass


@get_identifiers.register
def _(huffman_tree: HuffmanTree) -> dict[bytes, int]:
    """
    Given a huffman tree, the function assigns each byte value inside it a huffman encoding - a potentially shorter
    value based on the input data.
    The returned dictionary uses the original byte values as keys, and the shorter identifiers as values. Pay attention
    that the short identifiers may be more than one byte long, which is why they are represented as an integer (which
    allows up to four bytes).
    Of course, during encoding only the meaningful bits of the shorter identifiers are to be considered.

    :param huffman_tree: A huffman tree corresponding to a certain input. Short identifier for each of its leaf nodes
                         will be assigned according to its structure.
    :return: A dictionary mapping between the original byte values and the shorter identifiers that were assigned to
             them. Since the huffman tree only refers to byte values, the maximum amount of entries in the dictionary
             is 256.
    """
    # Create the dictionary:
    identifiers: dict[bytes, int] = {}

    # Use recursion to find leaf nodes:
    def dfs(node: Optional[HuffmanTree.Node], identifier: int):
        if node is not None:
            # if it's a leaf, assign an identifier
            if node.is_leaf():
                identifiers[node.char] = identifier
            # If not, assign 0 to left and 1 to right:
            else:
                dfs(node.left, identifier << 1)
                dfs(node.right, (identifier << 1) | 1)
    dfs(huffman_tree.root, 0)
    return identifiers


@get_identifiers.register
def _(bit_stream: bytes) -> dict[bytes, bytes]:
    """
    Given a bit stream as a bytes object, the function parses it and assigns every byte value from 0 to 255
    a unique but shorter identifier.
    The returned dictionary uses the shorter byte values as keys, and the original byte identifiers as values.

    :param bit_stream: A sequence of bytes that represent the huffman identifiers according to a pre-determined
                       structure.
    :return: A dictionary that maps short bit values to normal byte values.
    """
    # TODO
    pass


def turn_identifiers_into_bytes(identifiers: dict[bytes, int]) -> bytearray:
    """
    Given a dictionary that maps byte values from 0 to 255 to shorter identifiers, the function produces a bit stream
    that contains those identifiers. The bit stream is saved in python as a bytes object.
    The stream's length will vary depending on the identifiers, in order to save space as much as possible.

    The stream's format is the following:
    The first byte will always contain the number of identifiers encoded. There are 256 possible identifiers (in case
    all byte values are encoded), so the number of identifiers in the stream will be the first byte's value, plus one.
    Note that this doesn't allow for 0 identifiers. If an empty dictionary is given to the function, the result will
    always be an empty bytes object.

    The next byte value is the identifier key (the value that is encoded).
    The next half a byte (4 bits) will hold the length of the encoded identifier in BITS (not bytes). 4 bits allows
    for a maximum of 15 bits, or 32768 possible values for the identifier. This is enough values while also being pretty
    compact in terms of memory.
    The next bits will be the actual encoded value, and after them either the stream ends or the next identifier will be
    stored.

    :param identifiers: A dictionary mapping regular byte values to shorter values, which are stored as an integer for
                        simpler bit operations.
    :return: A bytes object that encodes these identifiers.
    :raises TypeError: If the argument isn't a dictionary mapping bytes to integers.
    :raises ValueError: If the amount of entries exceeds 256, or if the key of one of the entries contains multiple
                        bytes (only one is allowed).
    """
    # If the dictionary is empty, return an empty bytes object:
    if len(identifiers) == 0:
        return bytes()

    # Check that the dictionary has a maximum of 256 entries, and they all contain one byte as key:
    __validate_identifiers_dict(identifiers)

    # Initialize the bit buffer:
    bit_buffer: BitBuffer = BitBuffer()

    # Write the number of identifiers minus 1:
    identifiers_count = len(identifiers) - 1
    bit_buffer.insert_byte(bytes([identifiers_count]))

    # Insert the identifiers:
    for byte_val, short_encoding in identifiers.items():
        __insert_identifier_to_buffer(byte_val, short_encoding, bit_buffer)

    return bytes(bit_buffer)


def __insert_identifier_to_buffer(byte_val: bytes, short_encoding: int, buffer: BitBuffer) -> None:
    """
    Inserts the bits of the given encoding into the bit buffer.
    :param byte_val: The byte value that is encoded.
    :param short_encoding: The short encoding given to the byte value.
    :param buffer: The buffer that the identifier will be inserted into.
    """
    # Insert the byte value:
    buffer.insert_byte(byte_val)

    # Insert the number of bits the short encoding takes up as a 4 bit value:
    identifier_bits_len = short_encoding.bit_length() & 0xF
    for i in range(3, -1, -1):
        buffer.insert_bit((identifier_bits_len >> i) & 1)

    # Insert the actual bits of the value:
    for i in range(identifier_bits_len - 1, -1, -1):
        buffer.insert_bit((short_encoding >> i) & 1)


def __validate_identifiers_dict(identifiers: dict[bytes, int]) -> None:
    """
    Validates the type and length of the identifier dictionary.
    :param identifiers: A dictionary mapping regular byte values to shorter values, which are stored as an integer for
                        simpler bit operations.
    :raises TypeError: If the argument isn't a dictionary mapping bytes to integers.
    :raises ValueError: If the amount of entries exceeds 256, or if the key of one of the entries contains multiple
                        bytes (only one is allowed).
    """
    # Check type:
    if not isinstance(identifiers, dict):
        raise TypeError(f"Expected dictionary, got {type(identifiers)} instead")

    # Check entries count:
    elif len(identifiers) > 256:
        raise ValueError(f"The identifiers dictionary can only contain 256 entries max ({len(identifiers)} received)")

    # Check key, value types:
    for key, value in identifiers.items():
        # Key check:
        if not isinstance(key, bytes):
            raise TypeError(f"Dictionary should use `bytes` as key type (got {type(key)} instead)")
        elif len(key) != 1:
            raise ValueError(f"Dictionary keys should be one byte long (got {len(key)})")

        # Value check:
        if not isinstance(value, int):
            raise TypeError(f"Dictionary should use `int` as value type (got {type(value)} instead)")
