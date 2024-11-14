from compressors import Compressor
from util.bitbuffer import BitBuffer


class RleCompressor(Compressor):
    """
    Compression class - Run Length Encoding.
    """

    def encode(self, input_data: bytes) -> bytes:
        """
        Encodes the input data using the Run Length Encoding algorithm.
        :param input_data: The data bytes that will be compressed.
        :return: A compressed version of the input data.
        """
        if len(input_data) == 0:
            return bytes()

        # Initialize the buffer:
        buffer: BitBuffer = BitBuffer()
        current_byte, repetitions = input_data[0], 1

        for byte_val in input_data[1:]:
            if current_byte != byte_val:
                # Insert the byte value and the repetitions count:
                buffer.insert_bits(current_byte, 8)
                buffer.insert_bits(repetitions, 8)

                # Initialize byte and repetitions:
                current_byte, repetitions = byte_val, 1
            else:
                repetitions += 1

        # Add the current byte (it was skipped):
        buffer.insert_bits(current_byte, 8)
        buffer.insert_bits(repetitions, 8)

        return bytes(buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the compressed data according to the RLE algorithm.
        :param compressed_data: The data that was compressed by the RLE class.
        :return: The original content of the data, prior to being compressed according to the RLE algorithm.
        :raises ValueError: If the compressed data has invalid format (i.e: it was tampered with or compressed according
                            to a different method).
        """
        # The length of the data in bytes has to be even, as for every run there is one byte for the byte value and
        # another for the repetitions:
        if len(compressed_data) % 2 == 1:
            raise ValueError('Invalid data to be decoded by the RLE algorithm')

        # Initialize the buffer:
        buffer: BitBuffer = BitBuffer()

        # Decode the data:
        for i in range(0, len(compressed_data), 2):
            byte_val, repetitions = compressed_data[i], compressed_data[i + 1]
            for _ in range(repetitions):
                buffer.insert_bits(byte_val, 8)

        return bytes(buffer)
