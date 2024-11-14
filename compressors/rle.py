from compressors import Compressor
from util.bitbuffer import BitBuffer


class RLE(Compressor):
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
        pass
