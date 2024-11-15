import rich
import typer
from pathlib import Path
from rich.table import Table
from compressors import Compressor
from rich.progress import SpinnerColumn, Progress, TextColumn
from cli.benchmark import BenchmarkResults, CompressorBenchmark


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


def get_benchmark_table(benchmark_results: BenchmarkResults) -> Table:
    """
    Given the results of out benchmark, the function prints them in a nice table.
    :param benchmark_results: The results of the benchmark.
    """
    # Check for compression data:
    is_compressing = benchmark_results.compression_ratio is not None

    # Create columns for the main table:
    main_table = Table(title='Benchmark Results', style="bold blue", title_style="bold white")
    main_table.add_column('Total Time (s)')
    main_table.add_column('Memory Usage (MiB)')
    if is_compressing:
        main_table.add_column('Compression Ratio')
        main_table.add_column('Space Saving')

    # Add memory sub-table:
    memory_table = Table(show_edge=False, show_lines=False)
    memory_table.add_column('Min')
    memory_table.add_column('Avg')
    memory_table.add_column('Max')

    # Add the actual data:
    memory_data = f"{benchmark_results.min_mem:.2f}", f"{benchmark_results.avg_mem:.2f}", f"{benchmark_results.max_mem:.2f}"
    memory_table.add_row(*memory_data)

    row = [f"{benchmark_results.runtime_results.cumtime:.4f}", memory_table]
    if is_compressing:
        # Show space-saving as percentage:
        row += [f"{benchmark_results.compression_ratio:.2f}", f"{(100 * benchmark_results.space_saving):.2f} %"]
    main_table.add_row(*row)

    return main_table


def execute_compressor(
        compressor: Compressor, compressed_file_extension: str, input_path: Path, output_path: Path, is_compressing: bool,
        benchmark: bool = True
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
        if benchmark:
            # Benchmark and print results:
            compressor_benchmark = CompressorBenchmark(compressor)
            output_data, benchmark_results = compressor_benchmark(input_data, is_compressing)
            table = get_benchmark_table(benchmark_results)
            rich.print(table)
        else:
            output_data: bytes = compressor.encode(input_data) if is_compressing else compressor.decode(input_data)

        # Write to output file:
        progress.add_task(description="Writing to output file...", total=None)
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)

        rich.print(f"[bold green]File {'' if is_compressing else 'de'}compressed successfully![/bold green]")
