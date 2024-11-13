import rich
import typer
from pathlib import Path
from typing_extensions import Annotated
from compressors.lzw import LzwCompressor
from cli.shared_behavior import execute_compressor
from compressors.lzw.memory_limits import OutOfMemoryStrategy, TooManyEncodingsException

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
            min=1, show_default=False,
            help="The LZW algorithm uses a dictionary during compression. This parameter controls the maximum "
                 "amount of entries in this dictionary.\nThe command will fail if not enough entries were given "
                 "in order to complete the algorithm."
        )],
        memory_strategy: Annotated[OutOfMemoryStrategy, typer.Option(
            show_default=True, case_sensitive=False,
            help="The LZW algorithm is a dictionary-based compression method. In order to not explode your computer, "
                 "the program limits the amount of memory the dictionary can have.\nFor this reason, something must be "
                 "done if the dictionary runs out of memory:"
                 "\n\n\t"
                 "- ABORT: Stops the execution of the command, doesn't complete the compression."
                 "\n\n\t"
                 "- STOP_STORE: The command will continue compressing the file, but won't add new data to the"
                 " dictionary. This means the maximum dictionary size won't be exceeded, however the resulting "
                 "compressed file won't be as small as it could have been if enough memory had been given."
                 "\n\n\t"
                 "- USE_MINIMUM_REQUIRED: The program will continue compressing the file as usual, but will dynamically "
                 "increase 'max_dict_size' if it runs out of memory. This approach will exceed the original value of "
                 "'max_dict_size', but will use the minimum amount of entries possible."
        )] = OutOfMemoryStrategy.ABORT
) -> None:
    """
    Compresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    # In case the compressor throws a 'TooManyEncodingsException', catch it and print to the user a more elegant
    # message:
    compressor = LzwCompressor(max_dict_size, memory_strategy)
    try:
        execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=True)
    except TooManyEncodingsException as e:
        rich.print("[bold red]LZW dictionary ran out of memory[/bold red]")
        raise typer.Abort(e)


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
) -> None:
    """
    Decompresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    # During decoding, we don't care about the memory:
    compressor = LzwCompressor(1, OutOfMemoryStrategy.ABORT)

    # Keep an eye out for ValueError, it is raised for an invalid format:
    try:
        execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=False)
    except ValueError:
        rich.print("[bold red]Invalid data given - cannot complete decompression[/bold red]")
        typer.Exit(1)
