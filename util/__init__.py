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

import typer
from pathlib import Path
from typing import Generator


def get_bit(b: bytes, offset: int) -> int:
    """
    Extracts a single bit from the bytes object.
    :param b: The bytes object that the bit will be extracted from.
    :param offset: The offset of the bit from the start of the bytes object.
    :return: The value of the bit at the given offset.
    """
    return (b[offset // 8] >> (7 - (offset % 8))) & 1


def read_bits(bitstream: bytes, offset: int, bits_num: int) -> int:
    """
    Reads the specified number of bits from the bitstream.
    :param bitstream: A collection of bits represented as a bytes object.
    :param offset: The offset from the start of the stream that the function will start reading from.
    :param bits_num: The number of bits that will be returned. The maximum possible bits are 32, above that bits will
                     be deleted from the result.
    :return: The specified bits in the stream as an integer. The last bit requested will be stored in the integer's
             least significant bit.
    :raises IndexError: If offset + bits_num > 8 * len(bitstream)
    """
    # Check index:
    if offset + bits_num > 8 * len(bitstream):
        raise IndexError("Requested bit range exceeds bitstream size.")

    # Initialize the result:
    result: int = 0

    # Read each bit:
    for i in range(bits_num):
        current_bit = get_bit(bitstream, offset + i)
        result = ((result << 1) | current_bit) & 0xFFFFFFFF

    return result


def bits_iterator(data: bytes) -> Generator[int, None, None]:
    """
    Given a bytes object, the function returns a generator iterating over each byte's bits, from the most significant
    bit to the least.
    :param data: Some bytes whose bits will be iterated over.
    :return: A generator iterating over the data's bits.
    """
    for byte in data:
        for bit_offset in range(7, -1, -1):
            yield (byte >> bit_offset) & 1


def validate_file_paths(compressed_file_extension: str, input_path: Path, output_path: Path, is_compressing: bool) -> None:
    """
    Validates the input and output paths.
    More precisely, ensures the following conditions are met:
        - The file extension of the input path (in case of decompression) or output path (in case of compression) ends
          with the given 'compressed_file_extension' parameter.
        - The input path and output path are not pointing to the same file.
    :param compressed_file_extension: The file extension that files which were compressed by an algorithm should end in.
    :param input_path: The path of the given input file.
    :param output_path: The path of the given output file.
    :param is_compressing: Whether the input file is going to be compressed (True) or decompressed (False).
    :raises typer.BadParameter: If one of the condition above isn't met.
    """
    # Check file extension:
    path_to_check = output_path if is_compressing else input_path
    if path_to_check.suffix != compressed_file_extension:
        raise typer.BadParameter(
            f"{'Output' if is_compressing else 'Input'} file must have the file extension '{compressed_file_extension}'"
        )

    # Check that the input file isn't the output file:
    if input_path == output_path:
        raise typer.BadParameter("Input file and output file cannot be the same")
