def get_bit(b: bytes, offset: int) -> int:
    """
    Extracts a single bit from the bytes object.
    :param b: The bytes object that the bit will be extracted from.
    :param offset: The offset of the bit from the start of the bytes object.
    :return: The value of the bit at the given offset.
    :raises IndexError: If offset is larger than the amount of bits in the bytes object.
    """
    # Check index:
    if offset >= 8 * len(b):
        raise IndexError(f"Offset {offset} is out of bounds of bytes object with {len(b)} bytes")

    byte_idx, bit_idx = offset // 8, offset % 8
    return (b[byte_idx] >> (7 - bit_idx)) & 1


def read_bits(bitstream: bytes, offset: int, bits_num: int) -> int:
    """
    Reads the specified number of bits from the bitstream.
    :param bitstream: A collection of bits represented as a bytes object.
    :param offset: The offset from the start of the stream that the function will start reading from.
    :param bits_num: The number of bits that will be returned. The maximum possible bits are 32, above that bits will
                     be deleted from the result.
    :return: The specified bits in the stream as an integer. The last bit requested will be stored in the integer's
             least significant bit.
    :raises IndexError: If offset + bits_num > 8 * len(bitstream)
    """
    # Check index:
    if offset + bits_num > 8 * len(bitstream):
        raise IndexError("Requested bit range exceeds bitstream size.")

    # Initialize the result:
    result: int = 0

    # Read each bit:
    for i in range(bits_num):
        current_bit = get_bit(bitstream, offset + i)
        result = ((result << 1) | current_bit) & 0xFFFFFFFF

    return result
