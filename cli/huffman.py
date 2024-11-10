import rich
import typer
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
from compressors.huffman import HuffmanCompressor
from rich.progress import Progress, SpinnerColumn, TextColumn

# The huffman sub-app:
huffman_app = typer.Typer(name="huff", no_args_is_help=True)

# The file extension given to files compressed using the HuffmanCompressor:
HUFFMAN_FILE_EXTENSION = '.huff'


@huffman_app.command(no_args_is_help=True)
def compress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed. It can be any type of file, as long as it is not the "
                 "provided output file."
        )],
        output_path: Annotated[Optional[Path], typer.Argument(
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help=f"The path that the program will write the compressed data to, must end in '{HUFFMAN_FILE_EXTENSION}',"
                 " and cannot be the input file."
        )]
) -> None:
    """
    Compresses a file using [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman encoding[/link].
    The compressed data will be saved in the provided output path, and not interfere with the input file's data.
    """
    # Check output file's file extension:
    if output_path.suffix != HUFFMAN_FILE_EXTENSION:
        raise typer.BadParameter(f"Output file must have the file extension '{HUFFMAN_FILE_EXTENSION}'")

    # Check if the input and output file paths are the same:
    if input_path == output_path:
        raise typer.BadParameter("Input file and output file cannot be the same")

    # Read uncompressed data:
    with rich.progress.open(input_path, 'rb', description="Reading input file...", transient=True) as input_file:
        input_data: bytes = input_file.read()

    with Progress(
        SpinnerColumn(spinner_name="bouncingBall"),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        # Encode data:
        progress.add_task(description="Encoding data...", total=None)
        huffman_encoder = HuffmanCompressor()
        encoded_data: bytes = huffman_encoder.encode(input_data)

        # Write to output file:
        progress.add_task(description="Writing to output file...", total=None)
        with open(output_path, 'wb') as output_file:
            output_file.write(encoded_data)

        rich.print("[bold green]File compressed successfully![/bold green]")
