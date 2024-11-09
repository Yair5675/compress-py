import util
from .tree import HuffmanTree
from collections import Counter
from compressors import Compressor
import compressors.huffman.identifiers
from util.bitbuffer import BitBuffer


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
        encoded_bytes: dict[bytes, identifiers.HuffmanEncoding] = huffman_tree.get_encodings()

        # Create a buffer that will store the compressed bits:
        bit_buffer: BitBuffer = identifiers.turn_identifiers_into_bits(encoded_bytes)

        # Replace byte values with their huffman encoding:
        for byte_val in input_data:
            encoding: identifiers.HuffmanEncoding = encoded_bytes[bytes([byte_val])]
            encoding.load_to_buffer(bit_buffer)

        # Since the compressed data's bit count may not be divisible by 8, zeroes will be added to its end. This could
        # add data accidentally, so as a precaution, we'll make the last byte equal the number of zeroes that were added
        # to the compressed data:
        added_zeroes = (8 - len(bit_buffer) % 8) % 8
        for i in range(added_zeroes):
            bit_buffer.insert_bit(0)
        bit_buffer.insert_byte(bytes([added_zeroes]))

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

        # Get the amount of padding added to the end of the compressed data:
        padding_length = compressed_data[-1]

        # Initialize a bit buffer and a variable holding the current encoded part:
        buffer: BitBuffer = BitBuffer()
        encoded_key: identifiers.HuffmanEncoding = identifiers.HuffmanEncoding(0, 0)
        offset: int = data_start_idx

        # Go over the bits. We skip the last byte that contains the padding length (the -1 in the parenthesis), and skip
        # the padding itself (-padding_length):
        while offset < 8 * (len(compressed_data) - 1) - padding_length:
            # Add the original byte values based on the currently held encoded_key:
            current_bit = util.get_bit(compressed_data, offset)
            encoded_key.bit_length += 1
            encoded_key.encoding = (encoded_key.encoding << 1) | current_bit

            original_byte: bytes = encodings.get(encoded_key)
            if original_byte is not None:
                buffer.insert_byte(original_byte)
                encoded_key.bit_length = 0
                encoded_key.encoding = 0
            offset += 1

        return bytes(buffer)
