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

import util
from .tree import HuffmanTree
from collections import Counter
from compressors import Compressor
from util.bitbuffer import BitBuffer
from compressors.huffman.encodings import HuffmanEncoding


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

        # Create the huffman tree and produce encodings from it:
        huffman_tree = HuffmanTree(frequencies)
        encoded_bytes: dict[bytes, HuffmanEncoding] = huffman_tree.get_encodings()

        # Create a buffer that will store the compressed bits of the tree and the rest of the data:
        bit_buffer: BitBuffer = huffman_tree.to_bits()

        # Replace byte values with their huffman encoding:
        for byte_val in input_data:
            encoding: HuffmanEncoding = encoded_bytes[bytes([byte_val])]
            encoding.load_to_buffer(bit_buffer)

        # Since the compressed data's bit count may not be divisible by 8, zeroes will be added to its end. This could
        # add data accidentally, so as a precaution, we'll make the last byte equal the number of zeroes that were added
        # to the compressed data:
        if len(input_data) > 0:
            added_zeroes = (8 - len(bit_buffer) % 8) % 8
            bit_buffer.insert_bits(added_zeroes, 8 + added_zeroes)

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

        # If it's nothing, return nothing:
        if len(compressed_data) == 0:
            return bytes()

        # Get encodings from the start of the data:
        huffman_tree, data_start_idx = HuffmanTree.from_bits(compressed_data)
        encodings = huffman_tree.get_encodings()

        # Make the encodings the keys in the dictionary and the original bytes the values:
        encodings = {encoding: byte for byte, encoding in encodings.items()}

        # Get the amount of padding added to the end of the compressed data:
        padding_length = compressed_data[-1]

        # Initialize a bit buffer and a variable holding the current encoded part:
        buffer: BitBuffer = BitBuffer()
        encoded_key: HuffmanEncoding = HuffmanEncoding(0, 0)
        offset: int = data_start_idx

        # Go over the bits. We skip the last byte that contains the padding length (the -1 in the parenthesis), and skip
        # the padding itself (-padding_length):
        while offset < 8 * (len(compressed_data) - 1) - padding_length:
            # Add the original byte values based on the currently held encoded_key:
            current_bit = util.get_bit(compressed_data, offset)
            encoded_key.bit_length += 1
            encoded_key.encoding = (encoded_key.encoding << 1) | current_bit

            if encoded_key in encodings:
                original_byte: bytes = encodings[encoded_key]
                buffer.insert_bits(original_byte[0], 8)
                encoded_key.bit_length = 0
                encoded_key.encoding = 0
            offset += 1

        return bytes(buffer)
