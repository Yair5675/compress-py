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

import rich
import typer
import cli.lzw
import functools
from rich import box
from pathlib import Path
from typing import Optional
from rich.table import Table
from compressors import Compressor
from typing_extensions import Annotated
from compressors.rle import RleCompressor
from cli.transforms import Transformation
from compressors.huffman import HuffmanCompressor
from concurrent.futures import ProcessPoolExecutor
from compressors.lzw import LzwCompressor, OutOfMemoryStrategy
from cli.benchmark import CompressorBenchmark, BenchmarkResults

compressors_to_test: tuple[tuple[str, Compressor, Optional[Transformation]], ...] = (
    ("Huffman Coding (no transformations)", HuffmanCompressor()),
    ("Huffman Coding (BWT + MTF)", HuffmanCompressor(), Transformation.BWT, Transformation.MTF),
    ("LZW (best compression rate, no transforms)",
     LzwCompressor(int(cli.lzw.DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.USE_MINIMUM_REQUIRED)),
    ("LZW (best compression rate, BWT + MTF)", 
     LzwCompressor(int(cli.lzw.DictionarySize.EXTRA_LARGE), OutOfMemoryStrategy.USE_MINIMUM_REQUIRED),
     Transformation.BWT, Transformation.MTF),
    ("LZW (medium memory usage)", LzwCompressor(int(cli.lzw.DictionarySize.MEDIUM), OutOfMemoryStrategy.STOP_STORE)),
    ("LZW (smallest memory usage)", LzwCompressor(int(cli.lzw.DictionarySize.SMALL), OutOfMemoryStrategy.STOP_STORE)),
    ("RLE (no transformations)", RleCompressor()),
    ("RLE (BWT + MTF)", RleCompressor(), Transformation.BWT, Transformation.MTF)
)


def test_with(input_path: Path, test_idx: int) -> BenchmarkResults:
    benchmark = CompressorBenchmark(compressors_to_test[test_idx][1])
    transforms: tuple[Transformation] = compressors_to_test[test_idx][2:]
    with open(input_path, 'rb') as input_file:
        data = input_file.read()
        for t in transforms:
            data = t.encode_data(data)
        results: tuple[bytes, BenchmarkResults] = benchmark(data, compress=True)
    return results[1]


def get_compression_color(space_saving: float) -> str:
    spectrum: tuple[tuple[float, str], ...] = (
        (0.4, "bright_green"),
        (0.15, "green"),
        (0., "yellow"),
        (float('-inf'), 'bright_red')
    )
    for start_point, color in spectrum:
        if space_saving >= start_point:
            return color

    return "white"  # Shouldn't ever reach this point


def get_info_table(results: tuple[tuple[str, BenchmarkResults]]) -> Table:
    info_table: Table = Table(
        title="Combined Benchmark Results", style="bold blue", title_style="bold white", box=box.ROUNDED,
        show_lines=True
    )
    info_table.add_column('Algorithm')
    info_table.add_column('Total Time (s)')
    info_table.add_column('Average Memory Usage (MiB)')
    info_table.add_column('Original Size (bytes)')
    info_table.add_column('Compressed Size (bytes)')
    info_table.add_column('Compression Ratio')
    info_table.add_column('Space Saving')

    for algo_name, result in results:
        data = [algo_name, f"{result.runtime_results.cumtime:.4f}", f"{result.avg_mem:.2f}", f"{result.org_size:,}", f"{result.compressed_size:,}"]

        # Color compression efficiency:
        compression_color = get_compression_color(result.space_saving)
        data += [f"[{compression_color}]{result.compression_ratio:.2f}[/{compression_color}]",
                 f"[{compression_color}]{(100 * result.space_saving):.2f} %[/{compression_color}]"]
        info_table.add_row(*data)
    return info_table


def compare_all(input_path: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, dir_okay=False, readable=True, writable=False, resolve_path=True,
            show_default=False,
            help="The path to the file that will be compressed using every algorithm in the program"
        )]) -> None:
    """
    Given a file, the method uses all compression algorithms on it and compares them based on multiple criteria.
    Pay attention this command only compares the algorithms on the file, and does not produce an output file.
    """
    # Benchmark all algorithms:
    with ProcessPoolExecutor() as executor:
        results: tuple[BenchmarkResults] = tuple(executor.map(
            functools.partial(test_with, input_path), range(len(compressors_to_test))
        ))
    
    # Add the names of the algorithm to the results:
    results = zip((name for name, *_ in compressors_to_test), results)
    
    # Sort them based on compression ratios:
    results: tuple[tuple[str, BenchmarkResults]] = tuple(sorted(
        results, key=lambda name_and_result: name_and_result[1].compression_ratio, reverse=True
    ))
    
    # Create a big table for all the algorithms:
    info_table = get_info_table(results)
    rich.print(info_table)
