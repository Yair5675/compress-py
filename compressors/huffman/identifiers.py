import util
from dataclasses import dataclass
from util.bitbuffer import BitBuffer


class InvalidIdentifiersFormat(Exception):
    """
    An exception referring to improper formatting of byte-to-huffman-encoding as a bitstream.
    """
    def __init__(self, message="Invalid formatting of byte values to huffman encodings"):
        super().__init__(message)


@dataclass
class HuffmanEncoding:
    # The length of the encoding in bits (necessary in case the encoding starts with 0):
    bit_length: int
    # The actual encoding:
    encoding: int

    def load_to_buffer(self, bit_buffer: BitBuffer) -> None:
        """
        Inserts the bits of the huffman encoding into the bit buffer.
        :param bit_buffer: A bit buffer that the huffman encoding's bits will be inserted to.
        """
        bit_buffer.insert_bits(self.encoding, max(1, self.bit_length))

    def __repr__(self) -> str:
        return str(bin(self.encoding)[2:]).zfill(self.bit_length)

    def __hash__(self):
        return (self.encoding << 10) | self.bit_length


def get_identifiers_from_bytes(bit_stream: bytes) -> tuple[dict[HuffmanEncoding, bytes], int]:
    """
    Given a bit stream as a bytes object, the function parses it and assigns every byte value from 0 to 255
    a unique huffman encoding.
    The returned dictionary uses the huffman encodings as keys, and the original byte values as values.
    :param bit_stream: A sequence of bytes that represent the huffman identifiers according to a pre-determined
                       format.
    :return: A dictionary that maps huffman encodings to normal byte values, and the encoding bits' end index (the index
             of the first bit that doesn't belong to the identifiers' bits).
    :raises InvalidIdentifiersFormat: If the bitstream doesn't abide by the format used when representing the mapping
                                      of byte values to huffman encodings as a bit stream.
    """
    # Initialize the dictionary:
    identifiers: dict[HuffmanEncoding, bytes] = {}

    # Empty bytes case:
    if len(bit_stream) == 0:
        return identifiers, 0

    # First byte is the number of identifiers encoded (minus one):
    identifiers_count = bit_stream[0] + 1

    # Extract the identifiers (initialize a bit index):
    bit_idx: int = 8
    for i in range(identifiers_count):
        try:
            # Get the value that's encoded:
            original_value = util.read_bits(bit_stream, bit_idx, 8)
            bit_idx += 8

            # Get the length of the huffman encoding in bits (next byte bits):
            encoding_len = util.read_bits(bit_stream, bit_idx, 8)
            bit_idx += 8

            # Get the actual encoding:
            encoding = util.read_bits(bit_stream, bit_idx, encoding_len)
            bit_idx += encoding_len

            # Insert to dictionary:
            identifiers[HuffmanEncoding(encoding_len, encoding)] = bytes([original_value])
        except IndexError:
            raise InvalidIdentifiersFormat()

    return identifiers, bit_idx


def turn_identifiers_into_bits(identifiers: dict[bytes, HuffmanEncoding]) -> BitBuffer:
    """
    Given a dictionary that maps byte values from 0 to 255 to huffman encodings, the function produces a bit stream
    that contains those encodings. The stream's length will vary depending on the encodings, in order to save as much
    space as possible.

    The stream's format is the following:
    The first byte will always contain the number of encodings in the stream. There are 256 possible encodings (in case
    all byte values are encoded), so the number of encodings in the stream will be the first byte's value, plus one.
    Note that this doesn't allow for 0 encodings. If an empty dictionary is given to the function, the result will
    always be an empty bytes object.

    The next byte value is the original byte's value (the value that is encoded).
    The next half a byte (4 bits) will hold the length of the huffman encoding in BITS (not bytes). 4 bits allows
    for a maximum of 15 bits, or 32768 possible values for the encoding. This is enough values while also being pretty
    compact in terms of memory.
    The next bits will be the actual huffman encoding, and after them either the stream ends or the next identifier will
    be stored.

    :param identifiers: A dictionary mapping regular byte values to huffman encodings.
    :return: A BitBuffer object holding the bits that describe the huffman encodings.
    :raises TypeError: If the argument isn't a dictionary mapping bytes to HuffmanEncoding objects.
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
    bit_buffer.insert_bits(identifiers_count, 8)

    # Insert the identifiers:
    for byte_val, short_encoding in identifiers.items():
        __insert_identifier_to_buffer(byte_val, short_encoding, bit_buffer)

    return bit_buffer


def __insert_identifier_to_buffer(byte_val: bytes, short_encoding: HuffmanEncoding, buffer: BitBuffer) -> None:
    """
    Inserts the bits of the given huffman encoding into the bit buffer, according to the formatting of huffman encodings
    as bits.
    :param byte_val: The byte value that is encoded.
    :param short_encoding: The short encoding given to the byte value.
    :param buffer: The buffer that the encoding will be inserted into.
    """
    # Insert the byte value:
    buffer.insert_bits(byte_val[0], 8)

    # Insert the number of bits the short encoding takes up as a full byte (and make sure bit_length is at least 1):
    buffer.insert_bits(max(1, short_encoding.bit_length), 8)

    # Insert the actual bits of the encoding:
    short_encoding.load_to_buffer(buffer)


def __validate_identifiers_dict(identifiers: dict[bytes, HuffmanEncoding]) -> None:
    """
    Validates the type and length of the 'encodings' dictionary.
    :param identifiers: A dictionary mapping regular byte values to HuffmanEncoding objects.
    :raises TypeError: If the argument isn't a dictionary mapping bytes to HuffmanEncoding objects.
    :raises ValueError: If the amount of entries exceeds 256, or if the key of one of the entries contains multiple
                        bytes (only one is allowed).
    """
    # Check type:
    if not isinstance(identifiers, dict):
        raise TypeError(f"Expected dictionary, got {type(identifiers)} instead")

    # Check entries count:
    elif len(identifiers) > 256:
        raise ValueError(f"The encodings dictionary can only contain 256 entries max ({len(identifiers)} received)")

    # Check key, value types:
    for key, value in identifiers.items():
        # Key check:
        if not isinstance(key, bytes):
            raise TypeError(f"Dictionary should use `bytes` as key type (got {type(key)} instead)")
        elif len(key) != 1:
            raise ValueError(f"Dictionary keys should be one byte long (got {len(key)})")

        # Value check:
        if not isinstance(value, HuffmanEncoding):
            raise TypeError(f"Dictionary should use `HuffmanEncoding` as value type (got {type(value)} instead)")
