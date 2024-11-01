from compressors import Compressor


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

        # TODO: Implement the algorithm

    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the given compressed data according to the huffman coding technique.
        Certain assumptions are made about the given data, so this function should only be
        used on data that was compressed using the `encode` method in the HuffmanCompressor class.
        :param compressed_data: Data that was compressed using the HuffmanCompressor class.
        :return: The decompressed bytes of the given data.
        """
        pass
