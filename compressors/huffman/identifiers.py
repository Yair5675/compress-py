from typing import Optional
from .tree import HuffmanTree
from functools import singledispatch


@singledispatch
def get_identifiers(arg) -> dict[bytes, bytes]:
    pass


@get_identifiers.register
def _(huffman_tree: HuffmanTree) -> dict[bytes, bytes]:
    """
    Given a huffman tree, the function assigns each byte value inside it a shorter byte code.
    The returned dictionary uses the original byte values as keys, and the shorter byte identifiers as values.
    :param huffman_tree: A huffman tree corresponding to a certain input. Short identifier for each of its leaf nodes
                         will be assigned according to its structure.
    :return: A dictionary mapping between the original byte values and the shorter byte values that were assigned to
             them. Since the huffman tree only refers to byte values, the maximum amount of entries in the dictionary
             is 256.
    """
    # Create the dictionary:
    identifiers = {}

    # Use recursion to find leaf nodes:
    def dfs(node: Optional[HuffmanTree.Node], identifier: bytes):
        if node is not None:
            # if it's a leaf, assign an identifier
            if node.is_leaf():
                identifiers[node.char] = identifier
            # If not, assign 0 to left and 1 to right:
            else:
                dfs(node.left, identifier << 1)
                dfs(node.right, (identifier << 1) | 1)
    dfs(huffman_tree.root, bytes(1))
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


def turn_identifiers_into_bytes(identifiers: dict[bytes, bytes]) -> bytes:
    """
    Given a dictionary that maps byte values from 0 to 255 to shorter byte values, the function produces a bit stream
    that contains those identifiers. The bit stream is saved in python as a bytes object.

    The stream will consist of 256 bytes always, even if there are fewer identifiers in the dictionary. Each byte
    at index 'i' from the start will hold the shortened byte value for the byte value i.

    As for the missing identifiers - byte values that don't have a corresponding shorter identifier will be given the
    same value, which will be different from any actual short byte value saved in the dictionary. Pay attention that
    although this value will be the same across identifier in a single bitstream, it is not guaranteed that it will be
    the same across multiple bitstreams. Different identifiers will result in different 'NO IDENTIFIER' byte value.

    :param identifiers: A dictionary mapping regular byte values to shorter byte values.
    :return: A bytes object that encodes these identifiers.
    """
    # TODO
    pass
