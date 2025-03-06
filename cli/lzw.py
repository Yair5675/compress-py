import rich
import typer
from enum import Enum
from pathlib import Path
from typing import Optional, List
from typing_extensions import Annotated
from cli.transforms import Transformation
from compressors.lzw import LzwCompressor
from cli.shared_behavior import execute_compressor
from compressors.lzw.memory_limits import OutOfMemoryStrategy, TooManyEncodingsException

# The file extension given to files compressed using the LZWCompressor:
LZW_FILE_EXTENSION = '.lzw'


class DictionarySize(str, Enum):
    """
    Choices for size of LZW dictionary.
    """
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    EXTRA_LARGE = "EXTRA_LARGE"
    CUSTOM = "CUSTOM"  # Prompt the user

    def __int__(self):
        match self:
            case DictionarySize.SMALL:
                return 1_000
            case DictionarySize.MEDIUM:
                return 10_000
            case DictionarySize.LARGE:
                return 100_000
            case DictionarySize.EXTRA_LARGE:
                return 1_000_000
            case DictionarySize.CUSTOM:
                return -1


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
        max_dict_size: Annotated[DictionarySize, typer.Option(
            '--dict_size', '-ds',
            show_default=True, case_sensitive=False,
            help="""The maximum size of the dictionary used in the compression algorithm:"""
                 "\n\n\t"
                 f"- SMALL: {int(DictionarySize.SMALL):_}"
                 "\n\n\t"
                 f"- MEDIUM: {int(DictionarySize.MEDIUM):_}"
                 "\n\n\t"
                 f"- LARGE: {int(DictionarySize.LARGE):_}"
                 "\n\n\t"
                 f"- EXTRA_LARGE: {int(DictionarySize.EXTRA_LARGE):_}"
                 "\n\n\t"
                 f"- CUSTOM: User given size, must be positive (0 not allowed)"
        )] = DictionarySize.MEDIUM,
        memory_strategy: Annotated[OutOfMemoryStrategy, typer.Option(
            '--memory-strategy', '-ms',
            show_default=True, case_sensitive=False,
            help="The action taken if the dictionary's memory isn't enough for the compression: "
                 "\n\n\t"
                 "- ABORT: Stops the execution of the command, doesn't complete the compression.\n"
                 "\n\n\t"
                 "- STOP_STORE: Stop adding entries. Will complete the compression but reduce its efficiency."
                 "\n\n\t"
                 "- USE_MINIMUM_REQUIRED: Increase dictionary size to the minimal amount needed to complete the compression."
        )] = OutOfMemoryStrategy.ABORT,
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
    Compresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    # Get dictionary size out of enum:
    if max_dict_size is DictionarySize.CUSTOM:
        dict_size = ask_dict_size()
    else:
        dict_size = int(max_dict_size)

    # In case the compressor throws a 'TooManyEncodingsException', catch it and print to the user a more elegant
    # message:
    compressor = LzwCompressor(dict_size, memory_strategy)
    try:
        execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=True, benchmark=benchmark, transforms=transforms)
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
        benchmark: Annotated[bool, typer.Option(
                    '--benchmark', '-b',
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
    Decompresses the input file according to the
    [link=https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch]Lempel-Ziv-Welch[/link] algorithm, and writes
    the output to the output file.
    """
    # During decoding, we don't care about the memory:
    compressor = LzwCompressor(1, OutOfMemoryStrategy.ABORT)

    # Keep an eye out for ValueError, it is raised for an invalid format:
    try:
        execute_compressor(compressor, LZW_FILE_EXTENSION, input_path, output_path, is_compressing=False, benchmark=benchmark, transforms=transforms)
    except ValueError:
        rich.print("[bold red]Invalid data given - cannot complete decompression[/bold red]")
        typer.Exit(1)


def ask_dict_size() -> int:
    """
    Asks the user for a dictionary size.
    :return: The custom dictionary size selected by the user.
    :raises typer.BadParameter: If the given value is invalid.
    """
    # Get value:
    value = typer.prompt("Enter custom dictionary size", type=int)

    # Check it's positive:
    if value <= 0:
        raise typer.BadParameter('Dictionary value must be positive')

    return int(value)
