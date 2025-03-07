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

import pytest
from typing import Optional
from collections import Counter
from util.bitbuffer import BitBuffer
from compressors.huffman.tree import HuffmanTree, HuffmanEncoding


def get_tree_from_data(data: bytes) -> HuffmanTree:
    frequencies: Counter = Counter(data)
    frequencies: list[int] = [frequencies[i] for i in range(256)]

    return HuffmanTree(frequencies)


def same_structure(n1: Optional[HuffmanTree.Node], n2: Optional[HuffmanTree.Node]) -> bool:
    """Checks if the structure of the roots is similar"""
    n1_none, n2_none = n1 is None, n2 is None
    if n1_none or n2_none:
        return n1_none and n2_none
    return same_structure(n1.right, n2.right) and same_structure(n1.left, n2.left)


def same_leaves(n1: Optional[HuffmanTree.Node], n2: Optional[HuffmanTree.Node]) -> bool:
    """Checks if the byte value of the leaves in the trees are the same"""
    n1_none, n2_none = n1 is None, n2 is None
    if n1_none or n2_none:
        return n1_none and n2_none

    if n1.is_leaf() ^ n2.is_leaf():  # One is a leaf and other isn't
        return False

    if n1.is_leaf():
        return n1.char == n2.char

    return same_leaves(n1.left, n2.left) and same_leaves(n1.right, n2.right)


@pytest.fixture
def example_tree() -> HuffmanTree:
    return get_tree_from_data(b"aaaaaaaabbbbbbbccccdd")


@pytest.fixture
def example_tree_and_encodings(example_tree) -> tuple[HuffmanTree, dict[bytes, HuffmanEncoding]]:
    encodings = {
        b'a': HuffmanEncoding(1, 0),
        b'b': HuffmanEncoding(2, 0b11),
        b'c': HuffmanEncoding(3, 0b101),
        b'd': HuffmanEncoding(3, 0b100)
    }
    return example_tree, encodings

@pytest.fixture
def example_tree_and_buffer(example_tree) -> tuple[HuffmanTree, BitBuffer]:
    expected_tree_bits: int = 0b000000110000000011011000010000000000110000000011011001000001100011000110001000
    buffer = BitBuffer()
    buffer.insert_bits(expected_tree_bits, 78)
    return example_tree, buffer


@pytest.fixture
def example_tree_and_nodes_info(example_tree) -> tuple[HuffmanTree, tuple[list[tuple[HuffmanTree.Node, bool, bool]], int]]:
    byte_0 = bytes([0])
    nodes_info = [
        (HuffmanTree.Node(byte_0, 0, None, None), 1, 1),
        (HuffmanTree.Node(b'a', 0, None, None), 0, 0),
        (HuffmanTree.Node(byte_0, 0, None, None), 1, 1),
        (HuffmanTree.Node(byte_0, 0, None, None), 1, 1),
        (HuffmanTree.Node(b'd', 0, None, None), 0, 0),
        (HuffmanTree.Node(b'c', 0, None, None), 0, 0),
        (HuffmanTree.Node(b'b', 0, None, None), 0, 0)
    ]
    return example_tree, (nodes_info, 78)


def test_to_bits(example_tree_and_buffer):
    tree, expected_bits = example_tree_and_buffer
    assert tree.to_bits() == expected_bits


def test_parse_nodes_data(example_tree_and_nodes_info):
    tree, nodes_info = example_tree_and_nodes_info
    given_info = HuffmanTree._HuffmanTree__parse_nodes_data(bytes(tree.to_bits()))

    assert given_info == nodes_info


def test_form_root_node(example_tree_and_nodes_info):
    tree, (nodes_info, _) = example_tree_and_nodes_info
    constructed_root = HuffmanTree._HuffmanTree__form_root_node(nodes_info)
    
    assert same_leaves(tree.root, constructed_root) and same_structure(tree.root, constructed_root)
    
    
def test_from_bits(example_tree):
    org_encodings = example_tree.get_encodings()
    
    deserialized_tree, _ = HuffmanTree.from_bits(bytes(example_tree.to_bits()))
    deserialized_encodings = deserialized_tree.get_encodings()
    
    assert org_encodings == deserialized_encodings


def test_get_encodings(example_tree_and_encodings):
    tree, encodings = example_tree_and_encodings
    assert tree.get_encodings() == encodings
