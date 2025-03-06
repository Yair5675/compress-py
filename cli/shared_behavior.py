import util
import rich
from pathlib import Path
from typing import Optional
from compressors import Compressor
from cli.transforms import Transformation
from cli.benchmark import CompressorBenchmark
from rich.progress import SpinnerColumn, Progress, TextColumn


def execute_compressor(
        compressor: Compressor, compressed_file_extension: str, input_path: Path, output_path: Path, is_compressing: bool,
        benchmark: bool = True, transforms: Optional[list[Transformation]] = None
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
    :param benchmark: If true, the compressor is executed while being tested (its runtime speed and memory usage is
                      recorded). This information will then be printed to the screen.
    :param transforms: Pre-compression transformations. If decompressing, they will be executed in reverse.
    """
    # Validate paths:
    util.validate_file_paths(compressed_file_extension, input_path, output_path, is_compressing)

    # Read input data:
    with rich.progress.open(input_path, 'rb', description="Reading input file...", transient=True) as input_file:
        input_data: bytes = input_file.read()

    with Progress(
            SpinnerColumn(spinner_name="bouncingBall"),
            TextColumn("[progress.description]{task.description}"),
            transient=True
    ) as progress:
        # If there are pre-compression transformations, encode/decode with them:
        if transforms is not None:
            transforms = transforms if is_compressing else reversed(transforms)
            for transform in transforms:
                task_id = progress.add_task(
                    description=f"Computing {transform.value if is_compressing else 'inverse ' + transform.value}..."
                )
                input_data = transform.encode_date(input_data) if is_compressing else transform.decode_date(input_data)
                progress.remove_task(task_id)
        # Compress or decompress the file:
        progress.add_task(description=f"{'Encoding' if is_compressing else 'Decoding'} data...", total=None)
        if benchmark:
            # Benchmark and print results:
            compressor_benchmark = CompressorBenchmark(compressor)
            output_data, benchmark_results = compressor_benchmark(input_data, is_compressing)
            table = benchmark_results.get_benchmark_table()
            rich.print(table)
        else:
            output_data: bytes = compressor.encode(input_data) if is_compressing else compressor.decode(input_data)

        # Write to output file:
        progress.add_task(description="Writing to output file...", total=None)
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)

        rich.print(f"[bold green]File {'' if is_compressing else 'de'}compressed successfully![/bold green]")
