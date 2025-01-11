import pstats
from typing import Optional
from rich.table import Table
from cProfile import Profile
from functools import partial
from dataclasses import dataclass
from compressors import Compressor
from memory_profiler import memory_usage


@dataclass(init=False)
class BenchmarkResults:
    # Stats about the runtime of the encode/decode method used in the benchmark:
    runtime_results: pstats.FunctionProfile

    # Memory usage over time:
    memory_interval: float
    memory_usage_over_time: list[float]
    max_mem: float
    min_mem: float
    avg_mem: float

    # Results regarding compression efficiency:
    compression_ratio: Optional[float]
    space_saving: Optional[float]

    def __init__(
            self, runtime_data: pstats.FunctionProfile, memory_data: list[float], memory_interval: float,
            data_size: Optional[tuple[int, int]]
    ) -> 'BenchmarkResults':
        """
        Initializes the BenchmarkResults object.
        :param runtime_data: Data regarding the performance of the algorithm, represented as a pstats.FunctionProfile
                             object.
        :param memory_data: A sequence of memory usage values. This sequence represent the memory usage of the function,
                            measured at different intervals (time difference between each measurement is the
                            'memory_interval' parameter).
        :param memory_interval: The time interval between each memory measurement.
        :param data_size: A tuple containing the original size of the data and the compressed size of the data, in this
                          order. This parameter only makes sense when compressing, hence why it is optional.
        """
        # Set attributes:
        self.memory_interval = memory_interval
        self.runtime_results = runtime_data
        self.memory_usage_over_time = memory_data

        # Calculate minimum, maximum and average memory usage (not using builtin method since it's less efficient):
        self.min_mem, self.max_mem, self.avg_mem = float('inf'), float('-inf'), 0
        for m in self.memory_usage_over_time:
            self.min_mem = min(m, self.min_mem)
            self.max_mem = max(m, self.max_mem)
            self.avg_mem += m

        # Handle cases without memory data:
        if len(memory_data) == 0:
            self.min_mem, self.max_mem, self.avg_mem = 0, 0, 0
        else:
            self.avg_mem /= len(self.memory_usage_over_time)

        # Calculate compression ratio and space saving
        self.compression_ratio = None
        self.space_saving = None
        if data_size is not None and data_size[0] > 0 and data_size[1] > 0:
            self.compression_ratio = data_size[0] / data_size[1]  # Uncompressed / compressed
            self.space_saving = 1 - (data_size[1] / data_size[0])  # 1 - (compressed / uncompressed)

    def get_benchmark_table(self) -> Table:
        """
        Given the results of out benchmark, the function returns them in a nice table.
        """
        # Check for compression data:
        is_compressing = self.compression_ratio is not None

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
        memory_data = f"{self.min_mem:.2f}", f"{self.avg_mem:.2f}", f"{self.max_mem:.2f}"
        memory_table.add_row(*memory_data)

        row = [f"{self.runtime_results.cumtime:.4f}", memory_table]
        if is_compressing:
            # Show space-saving as percentage:
            row += [f"{self.compression_ratio:.2f}", f"{(100 * self.space_saving):.2f} %"]
        main_table.add_row(*row)

        return main_table


class CompressorBenchmark:
    """
    A class responsible for measuring different statistics about a compressor implementation.
    """
    __slots__ = (
        # The compressor algorithm being tested:
        '__comp',
    )

    def __init__(self, compressor: Compressor) -> 'CompressorBenchmark':
        if not isinstance(compressor, Compressor):
            raise TypeError(f"Expected compressor of type Compressor, got {type(compressor)} instead")

        self.__comp = compressor

    def __call__(self, input_data: bytes, compress: bool) -> (bytes, BenchmarkResults):
        """
        Compresses or decompresses the data given to the method, while tracking various stats such as speed and memory
        usage.
        :param input_data: The data that will be given to the compression/decompression algorithm. When receiving
                           the benchmark information, it is important to remember it is about activating the algorithm
                           on this particular data (and does not represent general stats for the algorithm).
        :param compress: Whether the benchmark should compress or decompress the input data.
        """
        # Profile runtime and memory:
        MEMORY_INTERVAL = 1e-3
        method_to_check = partial(self.compressor.encode if compress else self.compressor.decode, input_data)
        with Profile() as runtime_profiler:
            (memory_usage_data, output) = memory_usage(proc=method_to_check, interval=MEMORY_INTERVAL, retval=True)

        # Create the results (add data about compression if we encode):
        method_name = 'encode' if compress else 'decode'
        runtime_data = pstats.Stats(runtime_profiler).get_stats_profile().func_profiles[method_name]

        data_size = (len(input_data), len(output)) if compress else None
        results = BenchmarkResults(runtime_data, memory_usage_data, MEMORY_INTERVAL, data_size)

        return output, results

    @property
    def compressor(self):
        return self.__comp
