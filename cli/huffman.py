import rich
import typer
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
from compressors.huffman import HuffmanCompressor
from rich.progress import Progress, SpinnerColumn, TextColumn

# The huffman sub-app:
huffman_app = typer.Typer(name="huff", no_args_is_help=True)


@huffman_app.command(no_args_is_help=True)
def compress(
        input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=True, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed"
        )],
        output_path: Annotated[Optional[Path], typer.Option(
            "--output-path", "-o",
            file_okay=True, dir_okay=False, writable=True, resolve_path=True, show_default=False,
            help="The path that the program will write the compressed data to. If not provided, the program will write"
                 " the compressed data to the input file (deleting its original content)."
        )] = None
) -> None:
    """
    Compresses a file using [link=https://en.wikipedia.org/wiki/Huffman_coding]Huffman encoding[/link].
    """
    # Check if an output file path is provided, and warn in case it isn't:
    if output_path is None:
        typer.confirm(
            "Output file not provided, so compressed data will be written to input file. This will delete the "
            "original data and relace it with a compressed version of it. Do you want to proceed?", abort=True
        )
        output_path = input_path

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
