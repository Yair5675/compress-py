import util
from compressors import Compressor
from util.bitbuffer import BitBuffer


class RleCompressor(Compressor):
    """
    Compression class - Run Length Encoding on individual bits.
    """
    # The RLE will encode bit repetitions into blocks. Each block will hold the bit's value, followed by some
    # repetitions amount. Since the repetitions can never be 0, the saved amount will be repetitions - 1, which will
    # increase the repetitions we allow while using the same amount of bits:
    BLOCK_BITS: int = 4

    # Maximum amount of times a bit can be repeated (this number minus one will be saved in the block):
    MAX_REPETITIONS: int = 1 << (BLOCK_BITS - 1)

    @staticmethod
    def write_block(bit: int, repetitions: int, output: BitBuffer) -> None:
        """
        Writes a single RLE block to the output.
        :param bit: Some bit in the input data.
        :param repetitions: The number of times `bit` is repeated consecutively, assumed to be positive.
        :param output: The output buffer the block will be written to.
        """
        # Check bit and repetitions:
        if bit != 0 and bit != 1:
            raise ValueError(f"Invalid bit value: {bit}")
        if repetitions < 1 or repetitions > RleCompressor.MAX_REPETITIONS:
            raise ValueError(f"Invalid repetitions error, must be between 1 and {RleCompressor.MAX_REPETITIONS} ({repetitions} given)")

        # Subtract 1 from repetitions as it must be at least 1:
        repetitions -= 1

        # Combine the bit and the repetitions into a single block:
        block = (bit << (RleCompressor.BLOCK_BITS - 1)) | repetitions

        # Insert the block:
        output.insert_bits(block, RleCompressor.BLOCK_BITS)

    def encode(self, input_data: bytes) -> bytes:
        """
        Encodes the input data using the Run Length Encoding algorithm.
        :param input_data: The data bytes that will be compressed.
        :return: A compressed version of the input data.
        """
        if len(input_data) == 0:
            return bytes()

        # Initialize the buffer:
        output_buffer: BitBuffer = BitBuffer()

        prev_bit, repetitions = None, 0

        # Go over the bits:
        for bit in util.bits_iterator(input_data):
            # In case no bit was set:
            if repetitions == 0:
                prev_bit, repetitions = bit, 1
            # If it was, compare:
            elif repetitions < RleCompressor.MAX_REPETITIONS and prev_bit == bit:
                repetitions += 1
            else:
                RleCompressor.write_block(prev_bit, repetitions, output_buffer)
                prev_bit, repetitions = bit, 1
        # Write the last bit:
        RleCompressor.write_block(prev_bit, repetitions, output_buffer)

        # The compressed bits might be padded to complete a full byte, so we'll add a byte with this number:
        bits_to_skip = (8 - len(output_buffer) % 8) % 8

        return bytes((bits_to_skip,)) + bytes(output_buffer)

    def decode(self, compressed_data: bytes) -> bytes:
        """
        Decodes the compressed data according to the RLE algorithm.
        :param compressed_data: The data that was compressed by the RLE class.
        :return: The original content of the data, prior to being compressed according to the RLE algorithm.
        :raises ValueError: If the compressed data has invalid format (i.e: it was tampered with or compressed according
                            to a different method).
        """
        if len(compressed_data) == 0:
            return b''
        # Get the padding at the end from the first index:
        padding = compressed_data[0]

        # The number of bits in the compressed data has to be divisible by the block bits amount:
        if (8 * len(compressed_data) - padding - 8) % RleCompressor.BLOCK_BITS != 0:
            raise ValueError("Invalid or malformed data: Length isn't divisible by RLE block length")

        # Initialize buffer:
        output = BitBuffer()
        bits = util.bits_iterator(compressed_data[1:])
        bit_offset = 8

        for bit in bits:
            # If we reached the padding, break:
            if bit_offset + padding >= 8 * len(compressed_data):
                break

            # Get the repetitions amount by calling next on bits:
            repetitions = 0
            for _ in range(RleCompressor.BLOCK_BITS - 1):
                repetitions = (repetitions << 1) | next(bits)

            # Add 1 to repetitions as the current value can't be 0:
            repetitions += 1

            # Write the bit's value to the output repeated:
            bit_repeated = (1 << repetitions) - 1 if bit else 0
            output.insert_bits(bit_repeated, repetitions)

            # Add to bit_offset:
            bit_offset += RleCompressor.BLOCK_BITS

        return bytes(output)
