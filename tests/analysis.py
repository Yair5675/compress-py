# TODO:
#  [*] - Create some class that collects input size, compressed size, time it took to compress, memory usage data over
#        time, compression ratio and space saving
#  [ ] - Plot compression ratio relative to input size, color algorithms differently to make it more visually appealing
#  [ ] - Plot memory usage of all algorithms in a single plot to compare them. since multiple files are compressed with
#        the same algorithm, calculate the average memory usage graph for the same algorithm on multiple files and plot
#        this
#  [ ] - Rank algorithms for each corpora
#  [ ] - Save results to a CSV
import time
import pandas as pd
import memory_profiler
from functools import reduce
from compressors import Compressor
from cli.transforms import Transformation

# Time between memory measurements:
MEMORY_INTERVAL: float = 1e-4


def compress(c: Compressor, ts: list[Transformation], data: bytes):
    # Transform data if there are transformations:
    t_data: bytes = reduce(lambda d, t: t.encode_data(d), ts, data)
    
    # Compress and return:
    return c.encode(t_data)


def measure_algorithm(
        algorithm: str, compressor: Compressor, transforms: list[Transformation], data: bytes
) -> pd.DataFrame:
    # Start recording time and memory:
    start = time.perf_counter()
    (memory_usage, compressed_data) = memory_profiler.memory_usage(
        proc=(compress, (compressor, transforms, data), {}),
        interval=MEMORY_INTERVAL, retval=True
    )
    end = time.perf_counter()
    
    # Get sizes (set minimum to 1 to avoid division by 0):
    org_size = max(1, len(data))
    comp_size = max(1, len(compressed_data))
    
    # Form data frame:
    data_frame = pd.DataFrame({
        'Algorithm': algorithm,
        'Memory Measurements (s)': [i * MEMORY_INTERVAL for i in range(len(memory_usage))],
        'Memory usage (MiB)': memory_usage,
        'Compression duration (s)': end - start,
        'Original Size (bytes)': org_size,
        'Compressed Size (bytes)': comp_size,
        'Compression Ratio': org_size / comp_size,
        'Space Saving': 1 - (comp_size / org_size)
    })
    return data_frame
