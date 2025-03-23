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
df = pd.read_csv(f'{base_path}_1/message_arrival_times.csv')
df_2 = pd.read_csv(f'{base_path}_2/message_arrival_times.csv')
df_3 = pd.read_csv(f'{base_path}_3/message_arrival_times.csv')

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
    # Drop the maximum 100 values and minimum with nlargest and nsmallest
    df = df.drop(df['difference'].nlargest(10).index)
    df = df.drop(df['difference'].nsmallest(10).index)
    return df


df = calculate_time_differences(df)
df["difference_ms"] = df["difference"].to_numpy() / 1e6

df_2 = calculate_time_differences(df_2)
df_2["difference_ms"] = df_2["difference"].to_numpy() / 1e6

df_3 = calculate_time_differences(df_3)
df_3["difference_ms"] = df_3["difference"].to_numpy() / 1e6


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

def plot_normal_histogram(df, bins=1000):
    plt.figure(figsize=(10, 6))    
    plt.hist(df["difference_ms"], bins=bins, alpha=0.7)
    csfont = {'fontname':'Times New Roman', 'fontsize': 14}

    plt.xlabel("Delay (ms)", **csfont)
    plt.ylabel("Frequency", **csfont)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.show()    

hz_time = 1 / (int(run.split("_")[-1])) * 1000
    
def print_stats(df):
    print("Mean %: ", round(abs(df["difference_ms"].mean() - hz_time)*100 / hz_time, 3), "%") 
    print("Mean: ", round(df["difference_ms"].mean(), 3), "ms")
    print("Median: ", round(abs(df["difference_ms"].median() - hz_time)*100 / hz_time, 3), "%")
    print("Median: ", round(df["difference_ms"].median(), 3), "ms")
    print("Max: ", round(abs(df["difference_ms"].max() - hz_time)*100 / hz_time, 3), "%")
    print("Max: ", round(df["difference_ms"].max(), 3), "ms")
    print("Min: ", round(abs(df["difference_ms"].min() - hz_time)*100 / hz_time, 3), "%")
    print("Min: ", round(df["difference_ms"].min(), 3), "ms")
    print("99th percentile %: ", round(abs(df["difference_ms"].quantile(0.99) - hz_time)*100 / hz_time, 3), "%")
    print("99th percentile: ", round(df["difference_ms"].quantile(0.99), 3), "ms")
    print("99.9th percentile %: ", round(abs(df["difference_ms"].quantile(0.9999) - hz_time)*100 / hz_time, 3), "%")
    print("99.9th percentile: ", round(df["difference_ms"].quantile(0.9999), 3), "ms")
    
    print("Standard Deviation: ", round(df["difference_ms"].std(), 3), "ms")
    print("Arrived Messages: ", df.shape[0])
    print("Total Time: ", round((df["TimeArrival_ns"].iloc[-1] - df["TimeArrival_ns"].iloc[0]) / 1e9, 3), "s")
    print("\n")
    
print_stats(df)    
print_stats(df_2)
print_stats(df_3)
concatenated_df = pd.concat([df, df_2, df_3])
print_stats(concatenated_df)

plot_messages_per_second(df)
plot_normal_histogram(df)