from compressors import Compressor
from encoding_dict import EncodingDict


class LzwCompressor(Compressor):
    __slots__ = [
        # The dictionary used for encoding data:
        '__encoder_dict'
    ]

    def __init__(self, max_dict_size: int):
        # Set the encoder dictionary:
        self.__encoder_dict = EncodingDict(max_dict_size)

    def encode(self, input_data: bytes) -> bytes:
        """
        Compresses the input data based on the Lempel-Ziv-Welch algorithm.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed by the LZW algorithms.
        """
        pass

    def decode(self, compressed_data: bytes) -> bytes:
        pass
