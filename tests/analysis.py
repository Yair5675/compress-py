# TODO:
#  [*] - Create some class that collects input size, compressed size, time it took to compress, memory usage data over
#        time, compression ratio and space saving
#  [*] - Plot compression ratio relative to input size, color algorithms differently to make it more visually appealing
#  [*] - Plot memory usage of all algorithms in a single plot to compare them. since multiple files are compressed with
#        the same algorithm, calculate the average memory usage graph for the same algorithm on multiple files and plot
#        this
#  [ ] - Rank algorithms for each corpora
#  [ ] - Save results to a CSV
import time
from functools import reduce

import matplotlib.pyplot as plt
import memory_profiler
import pandas as pd

from cli.transforms import Transformation
from compressors import Compressor

# Time between memory measurements:
MEMORY_INTERVAL: float = 1e-2


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
        'Memory Measurements (s)': [[i * MEMORY_INTERVAL for i in range(len(memory_usage))]],
        'Memory usage (MiB)': [memory_usage],
        'Compression duration (s)': end - start,
        'Original Size (bytes)': org_size,
        'Compressed Size (bytes)': comp_size,
        'Compression Ratio': org_size / comp_size,
        'Space Saving': 1 - (comp_size / org_size)
    })
    return data_frame


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
