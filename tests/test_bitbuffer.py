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
from util.bitbuffer import BitBuffer


def load_insertions(insertions: list[int]) -> BitBuffer:
    """
    Loads insertions into a bitbuffer for tests.
    :param insertions: A 1D list containing the bits to insert (every even index) and the number of bits from it to
                       insert (every odd index).
    :return: A BitBuffer loaded according to the insertions list.
    """
    buffer = BitBuffer()

    for i in range(0, len(insertions), 2):
        bits_container, bits_num = insertions[i], insertions[i + 1]
        buffer.insert_bits(bits_container, bits_num)

    return buffer


@pytest.mark.parametrize('insertions, expected_value', [
    # Testing order of insertions (container has more bits present than the ones requested):
    ([0b101010, 5], "01010"),

    # More than 32 bits:
    ([0b100100111000101000101110001101010101001, 39], "100100111000101000101110001101010101001"),

    # Container "has fewer bits" than requested (zeroes should be put instead):
    ([0b111, 6], "000111"),

    # Trying to insert 0 bits:
    ([0b101010, 0], ""),

    ([0b101010, 6], '101010'),
    ([0b1010, 4, 0b1100, 4], '10101100'),
    ([0b11111111, 8, 0b11111111, 8, 0b1, 2], '111111111111111101'),
    ([(1 << BitBuffer.BITS_PER_INT) - 1, BitBuffer.BITS_PER_INT, 0b01, 2], f"{"1" * BitBuffer.BITS_PER_INT}01")

], ids=[
    "len(bits_container) > bits_num",
    "Over 32 bits",
    "len(bits_container) < bits_num",
    "Inserting 0 bits",
    "Insert 6 bits 101010",
    "Insert 4 bits 1010 then 4 bits 1100",
    "Insert 8 bits 11111111 then 8 bits 11111111 then 2 bits 01",
    f"Insert full integer ({BitBuffer.BITS_PER_INT} bits) and then 2 bits 01"
])
def test_insert_bits(insertions, expected_value: str):
    buffer = load_insertions(insertions)

    assert str(buffer) == expected_value


@pytest.mark.parametrize(
    "insertions, expected_length",
    [
        ([0b101, 3], 3),
        ([0b101, 3, 0b1100, 4], 7),
        ([0b1, 1], 1),
        ([0b11111111, 8, 0b10101010, 8], 16),
        ([0b1, 15], 15)
    ],
    ids=[
        "Insert 3 bits 101",
        "Insert 3 bits 101 then 4 bits 1100",
        "Insert 1 bit 1",
        "Insert 8 bits 11111111 then 8 bits 10101010",
        "Insert 15 bits 000...0001"
    ]
)
def test_len(insertions, expected_length):
    buffer = load_insertions(insertions)

    assert len(buffer) == expected_length


@pytest.mark.parametrize(
    "insertions, expected_bytes",
    [
        ([0b101010, 6], bytes([0b10101000])),  # Padding zeros at the end
        ([0b11111111, 8, 0b11001100, 8], bytes([0b11111111, 0b11001100])),  # No padding needed
        ([0b101010101010, 12], bytes([0b10101010, 0b10100000])),  # Only padding second byte
    ],
    ids=[
        "Insert 6 bits 101010 to bytes",
        "Insert 8 bits 11111111 then 8 bits 11001100 to bytes",
        "Insert 12 bits 101010101010 to bytes",
    ]
)
def test_bytes(insertions, expected_bytes):
    buffer = load_insertions(insertions)
    assert bytes(buffer) == expected_bytes


@pytest.mark.parametrize(
    "buffers, expected_value",
    [
        # Concatenating buffers with different sizes and bit patterns
        ([([0b101010, 6], [0b110011, 6]), '101010110011']),  # Simple concatenation of two buffers
        ([([0b1111, 4], [0b0000, 4]), '11110000']),  # Concatenating two buffers with 4 bits each
        ([([0b111, 3], [0b110, 3]), '111110']),  # Concatenating two buffers with 3 bits each
        ([([0b101010, 6], [0b1111, 4], [0b110, 3]), '1010101111110'])  # Concatenating three buffers
    ], ids=[
        "Concatenate two 6-bit buffers",
        "Concatenate two 4-bit buffers",
        "Concatenate two 3-bit buffers",
        "Concatenate three buffers of different sizes",
    ]
)
def test_concatenate(buffers, expected_value):
    buffers = [load_insertions(insertions) for insertions in buffers]
    concatenated_buffer = BitBuffer.concatenate(buffers)
    assert str(concatenated_buffer) == expected_value


@pytest.mark.parametrize(
    "data, expected_len, expected_repr",
    [
        # Empty bytes test:
        (b'', 0, ''),
        # Partial integer - not enough to be saved in deque:
        (b'\x01', 8, '00000001'),
        # Full integer but not more:
        (b'\xff' * (BitBuffer.BITS_PER_INT // 8), BitBuffer.BITS_PER_INT, '1' * BitBuffer.BITS_PER_INT),
        # Full AND partial integer:
        (b'\xff' * (BitBuffer.BITS_PER_INT // 8) + b'\x00', BitBuffer.BITS_PER_INT + 8, '1' * BitBuffer.BITS_PER_INT + 8 * '0'),
        # 2 Full integers:
        (b'\xff' * (BitBuffer.BITS_PER_INT // 4), 2 * BitBuffer.BITS_PER_INT, '11' * BitBuffer.BITS_PER_INT),
    ], ids=[
        "Empty data",
        "Partial integer - not enough to be saved in deque",
        "Full integer but not more",
        "Full AND partial integer",
        "2 Full integers"
    ]
)
def test_from_bytes(data: bytes, expected_len: int, expected_repr: str):
    # Get buffer from method:
    buffer = BitBuffer.from_bytes(data)
    
    # Compare length and repr:
    assert len(buffer) == expected_len
    assert repr(buffer) == expected_repr
    
    # Convert buffer to bytes and compare with the original data:
    assert data == bytes(buffer)


@pytest.mark.parametrize(
    "data, bit_offset, expected_bit",
    [
        (b'\x01', 0, 0),  # Single byte, first bit is 0
        (b'\x01', 7, 1),  # Single byte, last bit is 1
        (b'\x43', 0, 0),  # First bit of 01000011 (should be 0)
        (b'\x43', 1, 1),  # Second bit of 01000011 (should be 1)
        (b'\x43', 2, 0),  # Third bit of 01000011 (should be 0)
        (b'\x43', 3, 0),  # Fourth bit of 01000011 (should be 0)
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', 31, 0),  # 32nd bit (in first int)
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', 32, 0),  # 33rd bit (in second int)
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', 33, 1),  # 34th bit (in second int)
    ], ids=[
        "Single byte, first bit is 0",
        "Single byte, last bit is 1",
        "First bit of 01000011 (should be 0)",
        "Second bit of 01000011 (should be 1)",
        "Third bit of 01000011 (should be 0)",
        "Fourth bit of 01000011 (should be 0)",
        "Last bit in first block",
        "First bit in second block",
        "Second bit in second block"
    ]
)
def test_getitem(data, bit_offset, expected_bit):
    buffer = BitBuffer.from_bytes(data)
    assert buffer[bit_offset] == expected_bit


@pytest.mark.parametrize(
    "data, bit_offset, expected_bit",
    [
        (b'\x03', -1, 1),  # Last bit using negative index
        (b'\x03', -2, 1),  # Second last bit using negative index
        (b'\x03', -3, 0),  # Third last bit using negative index
        (b'\x03', -4, 0),  # Fourth last bit using negative index
        (b'\x01\x00\x00\x00\x40\x00\x00\x01', -1, 1),  # Last bit (in second int) using negative index
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', -31, 1),  # 31st from end, second block second bit
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', -32, 0),  # 32nd from end, second block first bit
        (b'\x01\x00\x00\x00\x40\x00\x00\x00', -33, 0),  # 33rd from end, last bit of first block
    ], ids=[
        "Last bit using negative index",
        "Second last bit using negative index",
        "Third last bit using negative index",
        "Fourth last bit using negative index",
        "Last bit (in second int) using negative index",
        "31st from end, second block second bit",
        "32nd from end, second block first bit",
        "33rd from end, last bit of first block"
    ]
)
def test_getitem_negative_index(data, bit_offset, expected_bit):
    buffer = BitBuffer.from_bytes(data)
    assert buffer[bit_offset] == expected_bit


@pytest.mark.parametrize(
    "data, bit_offset",
    [
        (b'\x01', 8),  # Out-of-bounds positive index
        (b'\x01', 9),  # Out-of-bounds positive index
        (b'\x01', 10),  # Out-of-bounds positive index
        (b'\x01', -9),  # Out-of-bounds negative index
    ], ids=[
        "Offset 8 for 8 bits",
        "Offset 9 for 8 bits",
        "Offset 10 for 8 bits",
        "Offset -9 for 8 bits"
    ]
)
def test_getitem_out_of_bounds(data, bit_offset):
    buffer = BitBuffer.from_bytes(data)
    with pytest.raises(IndexError):
        _ = buffer[bit_offset]
