from dataclasses import dataclass
from util.bitbuffer import BitBuffer


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
