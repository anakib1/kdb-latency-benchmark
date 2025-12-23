"""
Latency Analysis and Visualization Script

This script processes latency data from KDB+ timestamps, calculates percentiles,
and generates visualization plots.
"""

import os
import pandas as pd
from hdrh import histogram
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator
from pathlib import Path

# Configuration
THROUGHPUT = int(os.getenv('THROUGHPUT'))
EXPERIMENT_NAME = f'Experiment-{THROUGHPUT}-{datetime.now().isoformat()}'
RESULTS_DIR = f'../results/{EXPERIMENT_NAME}'
CSV_FILE = '../results/times.csv'
WINDOW_SIZE_SECONDS = 5
HISTOGRAM_MIN = 1
HISTOGRAM_MAX = 60_000_000  # 60 seconds in microseconds
HISTOGRAM_PRECISION = 3

# Percentiles to print
PERCENTILES_TO_PRINT = [50, 90, 99, 99.9, 99.99]

# Create results directory
Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)


def parse_kdb_timestamp(timestamp_str):
    """
    Parse KDB+ timestamp string to Python datetime.

    Args:
        timestamp_str: KDB+ timestamp string (e.g., "2024-01-01D12:00:00.000000")

    Returns:
        datetime object
    """
    return datetime.strptime(timestamp_str.replace('D', 'T')[:26], "%Y-%m-%dT%H:%M:%S.%f")


def parse_kdb_timespan(timespan_str):
    """
    Parse KDB+ timespan string to microseconds.

    Args:
        timespan_str: KDB+ timespan string (e.g., "0D00:00:00.123456")

    Returns:
        Total microseconds as integer
    """
    days, time = timespan_str.split('D')
    time_obj = datetime.strptime(time[:15], "%H:%M:%S.%f")

    total_microseconds = int(days) * 24 * 3600 * 1_000_000
    total_microseconds += time_obj.hour * 3600 * 1_000_000
    total_microseconds += time_obj.minute * 60 * 1_000_000
    total_microseconds += time_obj.second * 1_000_000
    total_microseconds += time_obj.microsecond

    return total_microseconds


def create_histogram_from_values(values):
    """
    Create an HDR histogram from a list of latency values.

    Args:
        values: List of latency values in microseconds

    Returns:
        HdrHistogram object
    """
    hist = histogram.HdrHistogram(HISTOGRAM_MIN, HISTOGRAM_MAX, HISTOGRAM_PRECISION)
    for value in values:
        hist.record_value(value)
    return hist


def calculate_windowed_statistics(df, window_size_seconds, percentiles):
    """
    Calculate latency statistics for time windows.

    Args:
        df: DataFrame with 'timestamp' and 'latency_us' columns
        window_size_seconds: Size of each time window in seconds
        percentiles: List of percentiles to calculate

    Returns:
        Tuple of (times, percentile_data) where percentile_data is a dict
        mapping percentile values to lists of latency values
    """
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    window_delta = timedelta(seconds=window_size_seconds)
    current_time = start_time

    times = []
    percentile_data = {p: [] for p in percentiles}

    while current_time < end_time:
        window_end = current_time + window_delta
        mask = (df['timestamp'] >= current_time) & (df['timestamp'] < window_end)
        window_latencies = df.loc[mask, 'latency_us']

        if not window_latencies.empty:
            window_hist = create_histogram_from_values(window_latencies)
            times.append(current_time)
            for percentile in percentiles:
                percentile_data[percentile].append(window_hist.get_value_at_percentile(percentile))

        current_time = window_end

    return times, percentile_data


def percentile_to_log_x(percentile):
    """
    Convert percentile to log-scale X-axis value for tail visualization.

    Args:
        percentile: Percentile value (0-100)

    Returns:
        Log-scale X-axis value
    """
    # Avoid log(0) by capping at 99.999
    percentile = min(percentile, 99.999)
    return -np.log10(max(1 - percentile / 100, 1e-12))


def print_percentiles(histogram_obj, percentiles):
    """
    Print latency values at specified percentiles.

    Args:
        histogram_obj: HdrHistogram object
        percentiles: List of percentile values to print
    """
    print("\n" + "=" * 60)
    print("LATENCY PERCENTILES")
    print("=" * 60)
    print(f"{'Percentile':<15} {'Latency (µs)':<20} {'Latency (ms)':<20}")
    print("-" * 60)

    for percentile in percentiles:
        latency_us = histogram_obj.get_value_at_percentile(percentile)
        latency_ms = latency_us / 1000.0
        print(f"{percentile:>6.3f}%      {latency_us:>15.2f}        {latency_ms:>15.3f}")

    print("=" * 60 + "\n")


def plot_timeline(times, percentile_data, output_path):
    """
    Plot latency timeline with requested percentiles.

    Args:
        times: List of timestamps
        percentile_data: Dictionary mapping percentile values to lists of latency values
        output_path: Path to save the plot
    """
    plt.figure(figsize=(12, 6))

    # Convert absolute timestamps to relative time (seconds since start)
    start_time = times[0] if times else None
    relative_times = [(t - start_time).total_seconds() for t in times] if start_time else []

    # Define line styles and colors for different percentiles
    line_styles = {
        50: ('-', 2),
        90: ('-', 2),
        99.9: ('-', 2),
        99.99: ('--', 2),
        99.999: ('--', 1.5)
    }

    colors = plt.cm.viridis(np.linspace(0, 1, len(percentile_data)))

    for idx, percentile in enumerate(sorted(percentile_data.keys())):
        style, width = line_styles.get(percentile, ('-', 2))
        label = f'{percentile}th percentile' if percentile in [50, 90] else f'{percentile} percentile'
        plt.plot(relative_times, percentile_data[percentile],
                label=label, linewidth=width, linestyle=style, color=colors[idx])

    plt.xlabel('Time since experiment start (seconds)', fontsize=12)
    plt.yscale('log')
    plt.ylabel('Latency (µs)', fontsize=12)
    plt.title('Latency Percentiles Every 5 Seconds', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_percentile_distribution(histogram_obj, output_path, percentiles_to_print):
    """
    Plot latency distribution across percentiles with tail expansion.

    Args:
        histogram_obj: HdrHistogram object
        output_path: Path to save the plot
        percentiles_to_print: List of percentiles to use for tick marks
    """
    # Generate percentile points for smooth curve
    percentiles = np.concatenate([
        np.linspace(0, 50, 10, endpoint=False),
        np.linspace(50, 90, 10, endpoint=False),
        np.linspace(90, 99, 10, endpoint=False),
        np.linspace(99, 99.9, 10, endpoint=False),
        np.linspace(99.9, 100, 10)
    ])

    latency_values = [histogram_obj.get_value_at_percentile(p) for p in percentiles]
    x_values = [percentile_to_log_x(p) for p in percentiles]

    # Tick marks at meaningful percentiles (use percentiles_to_print + 0 and 100)
    tick_percentiles = sorted(set([0] + list(percentiles_to_print) + [100]))
    tick_x = [percentile_to_log_x(p) for p in tick_percentiles]
    tick_labels = [f"{p}%" for p in tick_percentiles]

    plt.figure(figsize=(14, 5))
    plt.plot(x_values, latency_values, color='blue', linewidth=2)
    plt.xlabel('Percentile', fontsize=12)
    plt.ylabel('Latency (µs)', fontsize=12)
    plt.yscale('log')
    plt.title('Latency by Percentile Distribution (Tail-Expanded)', fontsize=14)
    plt.xticks(tick_x, tick_labels)

    # Add more y-ticks for better readability
    ax = plt.gca()

    # Calculate y-axis range from data
    min_latency = min(latency_values)
    max_latency = max(latency_values)

    # Generate major ticks: powers of 10 within the data range
    min_power = int(np.floor(np.log10(min_latency)))
    max_power = int(np.ceil(np.log10(max_latency)))
    major_ticks = [10**p for p in range(min_power, max_power + 1)]

    # Generate minor ticks: 2, 3, 4, 5, 6, 7, 8, 9 times powers of 10
    minor_ticks = []
    for p in range(min_power, max_power + 1):
        for multiplier in [2, 3, 4, 5, 6, 7, 8, 9]:
            tick_value = multiplier * (10**p)
            if min_latency <= tick_value <= max_latency:
                minor_ticks.append(tick_value)

    ax.set_yticks(major_ticks)
    ax.set_yticks(minor_ticks, minor=True)

    plt.grid(True, alpha=0.3, which='major')
    plt.grid(True, alpha=0.1, which='minor')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main():
    """Main execution function."""
    print(f"Processing latency data for experiment: {EXPERIMENT_NAME}")
    print(f"Results will be saved to: {RESULTS_DIR}")

    # Read and parse CSV data
    print(f"\nReading data from: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    df['timestamp'] = df['time'].apply(parse_kdb_timestamp)
    df['latency_us'] = df['latency'].apply(parse_kdb_timespan)

    print(f"Loaded {len(df)} latency measurements")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Calculate windowed statistics
    print(f"\nCalculating {WINDOW_SIZE_SECONDS}-second windowed statistics...")
    times, percentile_data = calculate_windowed_statistics(df, WINDOW_SIZE_SECONDS, PERCENTILES_TO_PRINT)

    # Create overall histogram
    print("Creating overall histogram...")
    overall_hist = create_histogram_from_values(df['latency_us'])

    # Print requested percentiles
    print_percentiles(overall_hist, PERCENTILES_TO_PRINT)

    # Generate plots
    print("Generating plots...")
    plot_timeline(times, percentile_data, f'{RESULTS_DIR}/timeline.png')
    plot_percentile_distribution(overall_hist, f'{RESULTS_DIR}/latency_percentile.png', PERCENTILES_TO_PRINT)

    print(f"Analysis complete! Results saved to: {RESULTS_DIR}")


if __name__ == '__main__':
    main()