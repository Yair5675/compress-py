import pstats
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
    memory_usage_over_time: list[float]
    max_mem: float
    min_mem: float
    avg_mem: float

    def __init__(self, runtime_data: pstats.FunctionProfile, memory_data: list[float]):
        # Set attributes:
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
            raise TypeError(f"Expected compressor of type Comressor, got {type(compressor)} instead")

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
        method_to_check = partial(self.compressor.encode if compress else self.compressor.decode, input_data)
        with Profile() as runtime_profiler:
            (memory_usage_data, output) = memory_usage(proc=method_to_check, interval=1e-2, retval=True)

        # Create the results:
        method_name = 'encode' if compress else 'decode'
        runtime_data = pstats.Stats(runtime_profiler).get_stats_profile().func_profiles[method_name]
        results = BenchmarkResults(runtime_data, memory_usage_data)

        return output, results

    @property
    def compressor(self):
        return self.__comp
