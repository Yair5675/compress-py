import rich
import typer
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated
from cli.transforms import Transformation
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
        )],
        benchmark: Annotated[bool, typer.Option(
            '--benchmark/--no-benchmark', '-b/-B', show_default=True,
            help="Whether the command should print information about the algorithm's performance and memory usage")
        ] = False,
        transforms: Annotated[List[Transformation], typer.Option(
            "--trans", '-t', show_default=True, case_sensitive=False,
            help=f"Pre-compression transformations, can potentially increase compression efficiency. The transformations "
                 f"will be computed sequentially in the same order they were given. Available transformations are:\n\n"
                 f"{'\n\n'.join([f"{a.value} - {a.help()}" for a in list(Transformation)])}"
        )] = None
) -> None:
    """
    Compresses the file according to the [link=https://en.wikipedia.org/wiki/Run-length_encoding]Run-Length encoding[/link] algorithm.
    This is an algorithm best suited for data with many repetitions. If this isn't the case, the compressed data may be larger than the original data.
    """
    # Initialize and execute the compressor:
    compressor = RleCompressor()
    execute_compressor(compressor, RLE_FILE_EXTENSION, input_path, output_path, is_compressing=True, benchmark=benchmark,
                       transforms=transforms)


def decompress(input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help=f"The path to the file that will be decompressed. Its file extension must be '{RLE_FILE_EXTENSION}'."
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
    Decompresses a file that was compressed using the program's [link=https://en.wikipedia.org/wiki/Run-length_encoding]RLE[/link] implementation.
    The command will only work on this program's implementation of Run-Length encoding, and will exit unsuccessfully if a file with invalid format will be given to it.
    """
    # Initialize and execute the compressor:
    compressor = RleCompressor()
    try:
        execute_compressor(compressor, RLE_FILE_EXTENSION, input_path, output_path, is_compressing=False, benchmark=benchmark, transforms=transforms)
    # Be careful of ValueError in case invalid data was given:
    except ValueError:
        rich.print("[bold red]Invalid RLE compressed data[/bold red]")
        raise typer.Exit(code=1)
