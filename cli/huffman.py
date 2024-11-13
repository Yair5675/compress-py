import typer
from pathlib import Path
import cli.shared_behavior
from typing_extensions import Annotated
from compressors.huffman import HuffmanCompressor

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
        )]
) -> None:
    """
    Compresses a file using [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman coding[/link].
    The compressed data will be saved in the provided output path, and not interfere with the input file's data.
    """
    cli.shared_behavior.execute_compressor(
        HuffmanCompressor(), HUFFMAN_FILE_EXTENSION, input_path, output_path, is_compressing=True
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
        )]
) -> None:
    """
    Decompresses a file that was compressed using the program's [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman Coding[/link] implementation.
    The command will only work on this program's implementation of Huffman coding, and will exit unsuccessfully if a file with invalid format will be given to it.
    """
    cli.shared_behavior.execute_compressor(
        HuffmanCompressor(), HUFFMAN_FILE_EXTENSION, input_path, output_path, is_compressing=False
    )
