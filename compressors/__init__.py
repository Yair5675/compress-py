from abc import ABC, abstractmethod


class Compressor(ABC):
    """
    An abstract class representing the basic requirements for a compressor.
    """

    @abstractmethod
    def encode(self, input_data: bytes) -> bytes:
        """
        Encodes the input data according to a certain compression algorithm.
        :param input_data: The input data before being compressed.
        :return: The input data after being compressed.
        """
        pass

    @abstractmethod
    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the compressed data according to a certain decompression algorithm. It should be noted
        that the decompression algorithm assumes the data was compressed in a certain way, and if not
        the method will fail.
        :param compressed_data: A data that was compressed according to a certain algorithm matching the
                                current decompression algorithm.
        :return: The decompressed data.
        """
        pass
