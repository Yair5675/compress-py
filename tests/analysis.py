# TODO:
#  [*] - Create some class that collects input size, compressed size, time it took to compress, memory usage data over
#        time, compression ratio and space saving
#  [*] - Plot compression ratio relative to input size, color algorithms differently to make it more visually appealing
#  [*] - Plot memory usage of all algorithms in a single plot to compare them. since multiple files are compressed with
#        the same algorithm, calculate the average memory usage graph for the same algorithm on multiple files and plot
#        this
#  [ ] - Rank algorithms for each corpora
#  [ ] - Save results to a CSV
import os
import time
from collections import namedtuple
from functools import reduce
from pathlib import Path

import matplotlib.pyplot as plt
import memory_profiler
import pandas as pd

from cli.transforms import Transformation
from compressors import Compressor

# Time between memory measurements:
MEMORY_INTERVAL: float = 1e-2

# Tuple that holds info about the compression of a corpus:
CorpusCompressionInfo = namedtuple("CorpusCompressionInfo", [
    # Name of the algorithm:
    'algorithm',
    # List of the original sizes of each file in the corpus
    'org_file_sizes',
    # List of the compressed sizes of each file in the corpus
    'compressed_file_sizes',
    # List of compression ratios
    'compression_ratios',
    # List of space savings
    'space_savings',
    # List of each compression's duration
    'compression_times',
    # List of peak memory usage
    'memory_peaks',
    # List of average memory usage
    'memory_avg'
])


def compress(c: Compressor, ts: list[Transformation], data: bytes):
    # Transform data if there are transformations:
    t_data: bytes = reduce(lambda d, t: t.encode_data(d), ts, data)
    
    # Compress and return:
    return c.encode(t_data)


def add_file_to_info(
        file_data: bytes, info: CorpusCompressionInfo, compressor: Compressor, transforms: list[Transformation]
):
    org_size = len(file_data)

    start = time.perf_counter()
    (memory_usage, compressed_data) = memory_profiler.memory_usage(
        proc=(compress, (compressor, transforms, file_data), {}), interval=MEMORY_INTERVAL, retval=True
    )
    end = time.perf_counter()

    avg_mem = 0 if len(memory_usage) == 0 else sum(memory_usage) / len(memory_usage)
    peak_mem = 0 if len(memory_usage) == 0 else max(memory_usage)

    comp_size = len(compressed_data)
    compression_ratio = org_size / comp_size
    space_saving = 1 - (comp_size / org_size)

    info.memory_avg.append(avg_mem)
    info.memory_peaks.append(peak_mem)
    
    info.org_file_sizes.append(org_size)
    info.compressed_file_sizes.append(comp_size)
    
    info.compression_times.append(end - start)
    info.compression_ratios.append(compression_ratio)
    info.space_savings.append(space_saving)


def measure_algorithm(
        algorithm: str, compressor: Compressor, transforms: list[Transformation], corpus_name: str
):
    # Get the directory:
    corpus_dir: Path = Path(__file__).parent.joinpath('testfiles', corpus_name)
    
    # Form info:
    info = CorpusCompressionInfo(algorithm, [], [], [], [], [], [], [])
    
    for file_name in os.listdir(corpus_dir):
        file_path = os.path.join(corpus_dir, file_name)
        if not os.path.isfile(file_path):
            continue
            
        with open(file_path, 'rb') as file:
            add_file_to_info(file.read(), info, compressor, transforms)
    
    return info


def plot_comp_vs_size(results: pd.DataFrame, subplot: plt.Axes, colors: dict[str, tuple[float, float, float, float]]):
    # Scatter the data:
    for i in range(len(results)):
        subplot.scatter(
            x=results.at[i, 'Original Size (bytes)'], y=results.at[i, 'Compression Ratio'],
            label=results.at[i, 'Algorithm'], color=colors[results.at[i, 'Algorithm']],
        )
    # Set titles, labels, legend:
    subplot.set_xlabel("Original Size (bytes)")
    subplot.set_ylabel("Compression Ratio")
    subplot.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
    subplot.set_title("Compression Ratio vs Input Size")


def plot_comp_ratios(results: pd.DataFrame, subplot: plt.Axes):
    # Sort by compression ratios:
    results.sort_values(by='Compression Ratio', ascending=False, inplace=True)

    subplot.set_ylabel("Compression Ratio")
    subplot.set_xlabel(None, fontsize=4)
    subplot.set_title("Average Compression Ratio")

    bar_width = 0.3
    subplot.bar(results['Algorithm'], results['Compression Ratio'], color="green", width=bar_width)


def plot_mem_usage(results: pd.DataFrame, subplot: plt.Axes, colors: dict[str, tuple[float, float, float, float]]):
    # Set labels, title and legend:
    subplot.set_title("Memory Usage Over Time")
    subplot.set_ylabel("Memory Usage (MiB)")
    subplot.set_xlabel("Memory Measurements (s)")

    # Set memory usage data, each algorithms gets a different line:
    for i in range(len(results)):
        x = results.at[i, 'Memory Measurements (s)'][0]
        y = results.at[i, 'Memory usage (MiB)'][0]
        subplot.plot(
            x, y, color=colors[results.at[i, 'Algorithm']], label=results.at[i, 'Algorithm']
        )
    subplot.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))


def plot_comp_time(results: pd.DataFrame, subplot: plt.Axes):
    # Sort by compression time:
    results.sort_values(by='Compression duration (s)', ascending=True, inplace=True)
    subplot.set_ylabel("Compression Time (s)")
    subplot.set_xlabel(None, fontsize=4)
    subplot.set_title("Average Compression Time")

    subplot.bar(results['Algorithm'], results['Compression duration (s)'], color='red', width=0.3)


def plot_results(results: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)

    # Create a color mapping for each algorithm:
    algorithms = results['Algorithm'].unique()
    color_map = plt.get_cmap("tab10")
    colors = {algorithm: color_map(i / len(algorithms)) for i, algorithm in enumerate(algorithms)}

    # Top left - Compression Ratio over Input Size:
    plot_comp_vs_size(results, axes[0, 0], colors)

    # Top right - Compression ratio bars sorted:
    plot_comp_ratios(results, axes[0, 1])

    # Bottom left - Memory usage over time:
    plot_mem_usage(results, axes[1, 0], colors)

    # Bottom right - Compression time sorted:
    plot_comp_time(results, axes[1, 1])

    plt.show()
