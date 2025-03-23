import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
from matplotlib.ticker import MaxNLocator
from scipy.ndimage import uniform_filter1d
from matplotlib.dates import num2date
import os
import seaborn as sns

# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Visualize benchmark data')
    parser.add_argument('--run', type=str, default="limit_test_1", 
                       help='Run identifier (folder name in data/)')
    parser.add_argument('--save', action='store_true',
                       help='Save plots to PNG files instead of displaying')
    return parser.parse_args()

# Get arguments
args = parse_arguments()
run = args.run
base_path = f'benchmark/data/{run}/'
# Load received messages from two CSV files and combine them
df_recv_1 = pd.read_csv(f'{base_path}/arrived_messages_1.csv')
df_recv_2 = pd.read_csv(f'{base_path}/arrived_messages_2.csv')
df_recv = pd.concat([df_recv_1, df_recv_2]).reset_index(drop=True)

# Load lost messages (IDs, Sent Time)
df_lost = pd.read_csv(f'{base_path}/invalid_ids_never_arrived.csv')

# Load system monitoring logs (ms, CPU%, Memory%)
df_monitor = pd.read_csv(f'{base_path}/system_usage.csv')

def plot_delay_with_lost_messages(df_recv, df_lost, max_points=10000):
    plt.figure(figsize=(12, 6))

    # Convert to NumPy arrays for faster processing
    message_ids = df_recv["ID"].to_numpy()
    delays = ((df_recv["Received Time"] - df_recv["Sent Time"]) / 1_000_000).to_numpy()

    # Downsample if too many points (keeping evenly spaced samples)
    if len(message_ids) > max_points:
        indices = np.linspace(0, len(message_ids) - 1, max_points, dtype=int)
        message_ids = message_ids[indices]
        delays = delays[indices]

    # Plot normal delay trend
    plt.plot(message_ids, delays, linestyle="-", marker=".", alpha=0.5, label="Message Delay (ms)")

    plt.xlabel("Message ID")
    plt.ylabel("Delay (ms)")
    plt.title(f"Message Delay Over Time")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    if args.save:
        plt.savefig(f"{base_path}/delay_with_lost_messages.png", dpi=300)
    else:
        plt.show()

def plot_messages_per_second(df_recv, window_size=10, max_hz=10_000):
    plt.figure()
    csfont = {'fontname':'Times New Roman', 'fontsize': 14}

    # Convert timestamps to seconds (assuming they are in nanoseconds)
    df_recv["Received Time (s)"] = (df_recv["Received Time"].to_numpy()) / 1_000_000_000
    # Bin timestamps into 1-second intervals
    df_recv["Time Bin"] = df_recv["Received Time (s)"].astype(int).to_numpy() * 100
    msg_per_sec = df_recv.groupby("Time Bin").size().to_numpy()

    # Create a time range for the x-axis
    time_range = np.arange(len(msg_per_sec))

    # Apply smoothing for better visualization
    smoothed_rate = uniform_filter1d(msg_per_sec, size=window_size)

    # Find the time `t_max_hz` where the expected function reaches 10,000 Hz
    t_max_hz = (max_hz - 100) / 100  # Solving 100x + 100 = 10,000 → x = (10,000 - 100) / 100

    # Plot measured messages per second
    plt.plot(time_range, smoothed_rate, linestyle="-", marker=".", alpha=0.7, label="Measured Messages per Second")

    # Plot theoretical function: 100x + 100 (extended to t_max_hz)
    theoretical_time_range = np.arange(len(time_range))
    theoretical_values = 100 * theoretical_time_range + 100

    # Trim theoretical values to only go up to 10,000 Hz
    theoretical_time_range = theoretical_time_range[theoretical_values <= max_hz]
    theoretical_values = theoretical_values[theoretical_values <= max_hz]

    plt.plot(theoretical_time_range, theoretical_values, linestyle="--", color="red", label="Expected: 100x + 100")

    plt.xlabel("Seconds", **csfont)
    plt.ylabel("Messages per Second", **csfont)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)

    # Add padding to the axis limits for a better visual appearance
    x_padding = 5  # Extra seconds of space
    y_padding = max_hz * 0.05  # 5% extra space

    plt.xlim(-x_padding, max(t_max_hz, max(time_range)) + x_padding)
    plt.ylim(-y_padding, max_hz + y_padding)

    if args.save:
        plt.savefig(f"{base_path}/messages_per_second_with_padding.png", dpi=300)
    else:
        plt.show()

def plot_lost_messages_histogram(df_lost, df_recv, bin_size=500):
    plt.figure()
    csfont = {'fontname':'Times New Roman', 'fontsize': 14}

    df_lost["Sent Time (s)"] = (df_lost["Sent Time"].to_numpy() - df_recv["Sent Time"][0]) / 1_000_000_000
    df_lost["Hz at Send"] = 100 + 100 * df_lost["Sent Time (s)"]

    # Define histogram bins for Hz
    min_hz = df_lost["Hz at Send"].min()
    max_hz = df_lost["Hz at Send"].max()

    bins = np.arange(min_hz, max_hz + bin_size, bin_size)

    # Create histogram with correct bins
    plt.hist(df_lost["Hz at Send"], bins=bins, color="red", alpha=0.7)

    plt.xlabel("Message Rate (Hz)", **csfont)
    plt.ylabel("Number of Lost Messages", **csfont)
    plt.grid(True, linestyle="--", alpha=0.6)

    if args.save:
        plt.savefig(f"{base_path}/lost_messages_histogram.png", dpi=300)
    else:
        plt.show()


def stats_first_lost_message(df_lost, df_recv):
    df_lost["Sent Time (s)"] = (df_lost["Sent Time"].to_numpy() - df_recv["Sent Time"][0]) / 1_000_000_000
    df_lost["Hz at Send"] = 100 + 100 * df_lost["Sent Time (s)"]

    # Find the first lost message
    first_lost_message = df_lost.iloc[0]
    first_lost_hz = first_lost_message["Hz at Send"]
    first_lost_time = first_lost_message["Sent Time (s)"]
    
    #print it to console
    print(f"First lost message at {first_lost_time:.2f} seconds with {first_lost_hz:.2f} Hz")
    
def hardware_resources(df_monitor):
    # Log the maximum difference between maximum and minimum for both CPU and Memory
    cpu_usage = df_monitor["CPU Usage"]
    memory_usage = df_monitor["Memory Usage"] 
    
    print(cpu_usage.max())
    print(memory_usage.max())
    
    cpu_diff = cpu_usage.quantile(0.99) - cpu_usage.quantile(0.01)
    memory_diff = memory_usage.quantile(0.99) - memory_usage.quantile(0.01)
    
    print(f"CPU Usage Difference: {cpu_diff:.2f}%")
    print(f"Memory Usage Difference: {memory_diff:.2f}%") 

# Run the function
hardware_resources(df_monitor)

plot_lost_messages_histogram(df_lost, df_recv)

plot_messages_per_second(df_recv)

stats_first_lost_message(df_lost, df_recv)