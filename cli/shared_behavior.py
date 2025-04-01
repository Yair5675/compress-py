#     Compress-py  A command-line interface for compressing files
#     Copyright (C) 2025  Yair Ziv
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import util
import rich
from pathlib import Path
from typing import Optional
from compressors import Compressor
from cli.transforms import Transformation
from cli.benchmark import CompressorBenchmark
from rich.progress import SpinnerColumn, Progress, TextColumn


def transform_data(data: bytes, transforms: list[Transformation], inverse: bool, progress: Progress) -> bytes:
    for t in reversed(transforms) if inverse else transforms:
        task_id = progress.add_task(description=f"Computing {'inverse ' + t.value if inverse else t.value}...")
        data = t.decode_data(data) if inverse else t.encode_data(data)
        progress.remove_task(task_id)
    return data


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
    if transforms is None:
        transforms = []
        
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
        # If we need to compress, compute the transforms BEFORE compression:
        if is_compressing:
            input_data = transform_data(input_data, transforms, False, progress)
            
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
        
        # If we need to decompress, compute the inverse transformations AFTER decompression:
        if not is_compressing:
            output_data = transform_data(output_data, transforms, True, progress)

        # Write to output file:
        progress.add_task(description="Writing to output file...", total=None)
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)

        rich.print(f"[bold green]File {'' if is_compressing else 'de'}compressed successfully![/bold green]")
