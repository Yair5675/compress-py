import rich
import typer
from pathlib import Path
from typing_extensions import Annotated
from compressors.rle import RleCompressor
from cli.shared_behavior import execute_compressor

RLE_FILE_EXTENSION = '.rle'


def compress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed. It can be any type of file, as long as it is not the "
                 "provided output file."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the compressed data to, must end in '{RLE_FILE_EXTENSION}',"
                 " and cannot be the input file."
        )]
) -> None:
    """
    Compresses the file according to the [link=https://en.wikipedia.org/wiki/Run-length_encoding]Run-Length encoding[/link] algorithm.
    This is an algorithm based suited for data with many repetitions. If this isn't the case, the compressed data may be larger than the original data.
    """
    # Initialize and execute the compressor:
    compressor = RleCompressor()
    execute_compressor(compressor, RLE_FILE_EXTENSION, input_path, output_path, is_compressing=True)


def decompress(input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help=f"The path to the file that will be decompressed. Its file extension must be '{RLE_FILE_EXTENSION}'."
        )],
        output_path: Annotated[Path, typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the decompressed data to. Its file extension can be anything, "
                 "but it must be different than the input file."
        )]
) -> None:
    """
    Decompresses a file that was compressed using the program's [link=https://en.wikipedia.org/wiki/Run-length_encoding]RLE[/link] implementation.
    The command will only work on this program's implementation of Run-Length encoding, and will exit unsuccessfully if a file with invalid format will be given to it.
    """
    # Initialize and execute the compressor:
    compressor = RleCompressor()
    try:
        execute_compressor(compressor, RLE_FILE_EXTENSION, input_path, output_path, is_compressing=True)
    # Be careful of ValueError in case invalid data was given:
    except ValueError:
        rich.print("[bold red]Invalid RLE compressed data[/bold red]")
        raise typer.Exit(code=1)
