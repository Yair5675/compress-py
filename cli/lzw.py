import typer
from pathlib import Path
from typing_extensions import Annotated
from compressors.lzw import LzwCompressor
from cli.shared_behavior import execute_compressor

# The file extension given to files compressed using the LZWCompressor:
LZW_FILE_EXTENSION = '.lzw'


# Add the algorithm to the compress and decompress apps:
def compress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed. It can be any type of file, as long as it is not the "
                 "provided output file."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the compressed data to, must end in '{LZW_FILE_EXTENSION}',"
                 " and cannot be the input file."
        )],
        max_dict_size: Annotated[int, typer.Argument(
            min=1, help="The LZW algorithm uses a dictionary during compression. This parameter controls the maximum "
                        "amount of entries in this dictionary.\nThe command will fail if not enough entries were given "
                        "in order to complete the algorithm."
        )]
) -> None:
    """
    Compresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    compressor = LzwCompressor(max_dict_size)
    execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=True)


def decompress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help=f"The path to the file that will be decompressed, must end in '{LZW_FILE_EXTENSION}' and cannot be the"
                 " provided output file."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the decompressed data to. It can be any type of file, but cannot "
                 "be the input file."
        )],
        max_dict_size: Annotated[int, typer.Argument(
            min=1, help="The LZW algorithm uses a dictionary during decompression. This parameter controls the maximum "
                        "amount of entries in this dictionary.\nThe command will fail if not enough entries were given "
                        "in order to complete the algorithm."
        )]
) -> None:
    """
    Decompresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    compressor = LzwCompressor(max_dict_size)
    execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=False)
