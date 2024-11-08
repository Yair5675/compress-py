import util
from .tree import HuffmanTree
from collections import Counter
from compressors import Compressor
import compressors.huffman.identifiers
from util.bitbuffer import BitBuffer, FULL_INT_MASK


class HuffmanCompressor(Compressor):
    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on the huffman coding technique.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed via huffman coding.
        :raises TypeError: If the input data isn't a `bytes` object.
        """
        # Type check:
        if not isinstance(input_data, bytes):
            raise TypeError(f'Expected type bytes, got {type(input_data)} instead')

        # Count the frequency of every byte value in the input data, and turn it into a list of size 256:
        frequencies: Counter = Counter(input_data)
        frequencies: list[int] = [frequencies[i] for i in range(256)]

        # Create the huffman tree and produce identifiers from it:
        huffman_tree = HuffmanTree(frequencies)
        encoded_bytes: dict[bytes, int] = huffman_tree.get_encodings()

        # Create a buffer that will store the compressed bits:
        bit_buffer: BitBuffer = BitBuffer()

        # Encode the huffman encodings:
        encodings_stream: bytes = identifiers.turn_identifiers_into_bytes(encoded_bytes)
        for stream_byte_val in encodings_stream:
            bit_buffer.insert_byte(bytes([stream_byte_val]))

        # Replace byte values with their huffman encoding:
        for byte_val in input_data:
            encoding: int = encoded_bytes[bytes([byte_val])]
            bit_buffer.insert_int(encoding)

        return bytes(bit_buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the given compressed data according to the huffman coding technique.
        Certain assumptions are made about the given data, so this function should only be
        used on data that was compressed using the `encode` method in the HuffmanCompressor class.
        :param compressed_data: Data that was compressed using the HuffmanCompressor class.
        :return: The decompressed bytes of the given data.
        """
        # Type check:
        if not isinstance(compressed_data, bytes):
            raise TypeError(f'Expected type bytes, got {type(compressed_data)} instead')

        # Get encodings from the start of the data:
        encodings, data_start_idx = identifiers.get_identifiers_from_bytes(compressed_data)

        # Initialize a bit buffer and a variable holding the current encoded part:
        buffer: BitBuffer = BitBuffer()
        encoded_key: int = 0
        offset: int = data_start_idx

        # Add the original byte values based on the currently held encoded_key:
        while offset < 8 * len(compressed_data):
            encoded_key = (encoded_key << 1) | util.get_bit(compressed_data, offset)
            encoded_key &= FULL_INT_MASK

            original_byte: bytes = encodings.get(encoded_key)
            if original_byte is not None:
                buffer.insert_byte(original_byte)

        return bytes(buffer)
