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
import numpy as np

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
    compressed_data = compress(compressor, transforms, file_data)
    end = time.perf_counter()

    comp_size = len(compressed_data)
    compression_ratio = org_size / comp_size
    space_saving = 1 - (comp_size / org_size)

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
    info = CorpusCompressionInfo(algorithm, [], [], [], [], [])

    for file_name in os.listdir(corpus_dir):
        file_path = os.path.join(corpus_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        with open(file_path, 'rb') as file:
            add_file_to_info(file.read(), info, compressor, transforms)

    return info


def plot_comp_vs_size(results: list[CorpusCompressionInfo], subplot: plt.Axes, colors: dict[str, tuple[float, float, float, float]]):
    # Scatter the data:
    for info in results:
        subplot.scatter(
            x=info.org_file_sizes, y=info.compression_ratios, color=colors[info.algorithm],
            label=info.algorithm
        )

    # Set titles, labels, legend:
    subplot.set_xscale('log')
    subplot.set_xlabel("Original Size (bytes)")
    subplot.set_ylabel("Compression Ratio")
    subplot.legend(fontsize=8, loc='upper left', bbox_to_anchor=(1, 1))
    subplot.set_title("Compression Ratio vs Input Size")


def plot_comp_ratios(results: list[CorpusCompressionInfo], subplot: plt.Axes):
    # Show all compression ratios per algorithm:
    bars_per_algo = len(results[0].compression_ratios)
    bar_x_pos = np.arange(len(results))

    algo_width = 0.7
    width_per_bar = algo_width / bars_per_algo

    # Plot the sub-bars:
    for i in range(bars_per_algo):
        # Compute the position of the ith bar in each algorithm:
        positions = bar_x_pos + i * width_per_bar - (algo_width / 2)
        subplot.bar(positions, [result.compression_ratios[i] for result in results], width=width_per_bar)

    # Set a square root scale:
    subplot.set_yscale('function', functions=(np.sqrt, lambda x: x ** 2))

    # Set algorithm names as labels:
    subplot.set_xticks(bar_x_pos)
    subplot.set_xticklabels([result.algorithm for result in results])

    subplot.set_ylabel("Compression Ratio")
    subplot.set_title("Compression Ratios + Average")


def plot_results(results: list[CorpusCompressionInfo]):
    fig, axes = plt.subplots(1, 2, figsize=(16, 10), constrained_layout=True)

    # Create a color mapping for each algorithm:
    color_map = plt.get_cmap("tab10")
    colors = {algorithm.algorithm: color_map(i / len(results)) for i, algorithm in enumerate(results)}

    # Top left - Compression Ratio over Input Size:
    plot_comp_vs_size(results, axes[0], colors)

    # Top right - Compression ratio bars sorted:
    plot_comp_ratios(results, axes[1])

    plt.show()
