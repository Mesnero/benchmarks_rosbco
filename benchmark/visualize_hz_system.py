import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description='Visualize benchmark data')
    parser.add_argument('--run', type=str, default="uds_big_1", 
                       help='Run identifier (e.g., "uds_big_1", "rosbridge")')
    return parser.parse_args()

# Get arguments
args = parse_arguments()
run = args.run
print(f"Processing benchmark data for run: {run}")
base_path = f'benchmark/data/{run}'
df = pd.read_csv(f'{base_path}/message_arrival_times.csv')


def plot_messages_per_second(df):
    # Convert nanoseconds to seconds
    df['time_seconds'] = np.floor((df['TimeArrival_ns'] - df['TimeArrival_ns'][0]) / 1e9).astype(int)

    # Count occurrences of each second
    message_counts = df['time_seconds'].value_counts().sort_index()

    # Convert index to numpy array
    time_seconds = message_counts.index.to_numpy()
    message_counts_values = message_counts.values

    # Plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(time_seconds, message_counts_values, marker='o')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Number of Messages')
    plt.title('Messages per Second')
    plt.grid(True)
    plt.show()
    
def calculate_time_differences(df):
    df['difference'] = df['TimeArrival_ns'].diff()
    return df


df = calculate_time_differences(df)
df["difference_ms"] = df["difference"].to_numpy() / 1e6


def line_chart_differences(df):
    df = df.dropna()
    # do not draw every point, too many
    df = df.iloc[::1000, :]
    plt.figure(figsize=(10, 6))
    plt.plot(df['difference_ms'])
    plt.xlabel('Index')
    plt.ylabel('Time Difference (ms)')
    plt.title('Time Differences Between Messages')
    plt.grid(True)
    plt.show()

def plot_normal_histogram(df, bins=500):
    plt.figure(figsize=(10, 6))    
    plt.hist(df["difference_ms"], bins=bins, alpha=0.7)

    plt.xlabel("Delay (ms)")
    plt.ylabel("Frequency")
    plt.title("Histogram of Total Transmission Time")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.show()    
    
def print_stats(df):
    print("Mean: ", df["difference_ms"].mean())
    print("Median: ", df["difference_ms"].median())
    print("Standard Deviation: ", df["difference_ms"].std())
    print("Max: ", df["difference_ms"].max())
    print("Min: ", df["difference_ms"].min())
    print("99th percentile: ", df["difference_ms"].quantile(0.99))
    print("99.9th percentile: ", df["difference_ms"].quantile(0.9999))
    print("95th percentile: ", df["difference_ms"].quantile(0.95))
    
    total_time_seconds = (df['TimeArrival_ns'].iloc[-1] - df['TimeArrival_ns'][0]) / 1e9
    print("Total time: ", total_time_seconds, " seconds")
    print("Total messages: ", len(df))
    print("Messages per second: ", len(df) / total_time_seconds)
    
print_stats(df)    
plot_messages_per_second(df)
line_chart_differences(df)
plot_normal_histogram(df)