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

import sys
import rich
import typer
from pathlib import Path
import cli.shared_behavior
from typing import List, Optional
from typing_extensions import Annotated
from cli.transforms import Transformation
from compressors.huffman import HuffmanCompressor
from compressors.huffman.tree import InvalidTreeFormat

# The file extension given to files compressed using the HuffmanCompressor:
HUFFMAN_FILE_EXTENSION = '.huff'


def compress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed. It can be any type of file, as long as it is not the "
                 "provided output file."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the compressed data to, must end in '{HUFFMAN_FILE_EXTENSION}',"
                 " and cannot be the input file."
        )],
        benchmark: Annotated[bool, typer.Option(
        '--benchmark/--no-benchmark', '-b/-B', show_default=True,
            help="Whether the command should print information about the algorithm's performance and memory usage")
        ] = False,
        transforms: Annotated[Optional[List[Transformation]], typer.Option(
            "--trans", '-t', show_default=False, case_sensitive=False,
            help=f"Pre-compression transformations, can potentially increase compression efficiency. The transformations "
                 f"will be computed sequentially in the same order they were given. Available transformations are:\n\n"
                 f"{'\n\n'.join([f"{a.value} - {a.help()}" for a in list(Transformation)])}"
        )] = None
) -> None:
    """
    Compresses a file using [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman coding[/link].
    The compressed data will be saved in the provided output path, and not interfere with the input file's data.
    """
    cli.shared_behavior.execute_compressor(
        HuffmanCompressor(), HUFFMAN_FILE_EXTENSION, input_path, output_path, is_compressing=True, benchmark=benchmark,
        transforms=transforms
    )


def decompress(input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help=f"The path to the file that will be decompressed. Its file extension must be '{HUFFMAN_FILE_EXTENSION}'."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the decompressed data to. Its file extension can be anything, "
                 "but it must be different than the input file."
        )],
        benchmark: Annotated[bool, typer.Option(
        '--benchmark/--no-benchmark', '-b/-B', show_default=True,
            help="Whether the command should print information about the algorithm's performance and memory usage")
        ] = False,
        transforms: Annotated[Optional[List[Transformation]], typer.Option(
            "--trans", '-t', show_default=False, case_sensitive=False,
            help=f"Pre-compression transformations, can potentially increase compression efficiency. The transformations "
                 f"will be computed sequentially in the REVERSE order they were given, to match the compression command."
                 f" Available transformations are:\n\n"
                 f"{'\n\n'.join([f"{a.value} - {a.help()}" for a in list(Transformation)])}"
        )] = None
) -> None:
    """
    Decompresses a file that was compressed using the program's [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman Coding[/link] implementation.
    The command will only work on this program's implementation of Huffman coding, and will exit unsuccessfully if a file with invalid format will be given to it.
    """
    try:
        cli.shared_behavior.execute_compressor(
            HuffmanCompressor(), HUFFMAN_FILE_EXTENSION, input_path, output_path, is_compressing=False, benchmark=benchmark,
            transforms=transforms
        )
    except InvalidTreeFormat:
        rich.print("[bold red]Malformed/invalid data given - cannot complete decompression[/bold red]", file=sys.stderr)
        typer.Exit(1)
