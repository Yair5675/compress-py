import rich
import typer
from pathlib import Path
from compressors import Compressor
from rich.progress import SpinnerColumn, Progress, TextColumn


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
            f"{"Output" if is_compressing else "Input"} file must have the file extension '{compressed_file_extension}'"
        )

    # Check that the input file isn't the output file:
    if input_path == output_path:
        raise typer.BadParameter("Input file and output file cannot be the same")


def execute_compressor(
        compressor: Compressor, compressed_file_extension: str, input_path: Path, output_path: Path, is_compressing: bool
) -> None:
    """
    Uses the compressor object to compress/decompress the bytes of the input file, and write the result into the output
    file.
    The function will perform two validations prior to execution: Ensuring proper file extension, and ensuring the input
    and output files are not the same.
    :param compressor: The Compressor object used in the compression/decompression. This object will determine the
                       algorithm used.
    :param compressed_file_extension: The file extension of files compressed by the given Compressor object. The
                                      function will ensure the input path (in case of decoding) or output path (in case
                                      of encoding) end with this extension.
    :param input_path: The path whose bytes will be read and served to the compressor object as input.
    :param output_path: The path of the file that the output will be written to.
    :param is_compressing: A flag telling the function whether it should compress the input file (True) or decompress it
                           (False).
    """
    # Validate paths:
    validate_file_paths(compressed_file_extension, input_path, output_path, is_compressing)

    # Read input data:
    with rich.progress.open(input_path, 'rb', description="Reading input file...", transient=True) as input_file:
        input_data: bytes = input_file.read()

    with Progress(
            SpinnerColumn(spinner_name="bouncingBall"),
            TextColumn("[progress.description]{task.description}"),
            transient=True
    ) as progress:
        # Compress or decompress the file:
        progress.add_task(description=f"{"Encoding" if is_compressing else "Decoding"} data...", total=None)
        output_data: bytes = compressor.encode(input_data) if is_compressing else compressor.decode(input_data)

        # Write to output file:
        progress.add_task(description="Writing to output file...", total=None)
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)

        rich.print("[bold green]File compressed successfully![/bold green]")
