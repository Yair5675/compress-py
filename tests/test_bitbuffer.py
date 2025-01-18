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
