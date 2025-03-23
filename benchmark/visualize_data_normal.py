import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Visualize benchmark data')
    parser.add_argument('--run', type=str, default="uds_big", 
                       help='Run identifier (e.g., "uds_big_1", "rosbridge")')
    return parser.parse_args()

# Get arguments
args = parse_arguments()
run = args.run
print(f"Processing benchmark data for run: {run}")
base_path = f'benchmark/data/{run}'
df = pd.read_csv(f'{base_path}_1/arrived_messages.csv')
df_2 = pd.read_csv(f'{base_path}_2/arrived_messages.csv')
df_3 = pd.read_csv(f'{base_path}_3/arrived_messages.csv')

def compute_timestamps(df, path):
    if not run.startswith("rosbridge"):
        df_ros_serialize = pd.read_csv(f'{path}/time_serialize.csv', skipinitialspace=True)
        df_ros_deserialize = pd.read_csv(f'{path}/time_deserialize.csv', skipinitialspace=True)
        # Merge new timestamps into the main dataframe
        df["Start Serialize ROS"] = df_ros_serialize["Sent Time"]
        df["End Serialize ROS"] = df_ros_serialize["Received Time"]
        df["Start Deserialize ROS"] = df_ros_deserialize["Sent Time"]
        df["End Deserialize ROS"] = df_ros_deserialize["Received Time"]
        
        df_py_serialize = pd.read_csv(f'{path}/serialize_time.csv', skipinitialspace=True)
        df_py_deserialize = pd.read_csv(f'{path}/deserialize_time.csv', skipinitialspace=True)
        
        df["Start Serialize Py"] = df_py_serialize["Start Time"]
        df["End Serialize Py"] = df_py_serialize["End Time"]
        df["Start Deserialize Py"] = df_py_deserialize["Start Time"]
        df["End Deserialize Py"] = df_py_deserialize["End Time"]
        
    else: # Just here to not break the code
        df["Start Serialize ROS"] = df["Sent Time"]
        df["End Serialize ROS"] = df["Received Time"]
        df["Start Deserialize ROS"] = df["Sent Time"]
        df["End Deserialize ROS"] = df["Received Time"]
        
        df["Start Serialize Py"] = df["Sent Time"]
        df["End Serialize Py"] = df["Received Time"]
        df["Start Deserialize Py"] = df["Sent Time"]
        df["End Deserialize Py"] = df["Received Time"]
    return df    


# Compute all delays
def compute_delays(df):
    # Start Time -> Start Serialize Py -> End Serialize Py -> Start Deserialize ROS -> End Deserialize ROS -> Start Serialize ROS -> End Serialize ROS -> Start Deserialize Py -> End Deserialize Py -> End Time
    df["Transmission Delay"] = (df["Start Serialize Py"] - df["Sent Time"]) / 1_000_000  # ms
    df["Serialization Time Py"] = (df["End Serialize Py"] - df["Start Serialize Py"]) / 1_000_000  # ms
    df["Send to ROS Delay"] = (df["Start Deserialize ROS"] - df["End Serialize Py"]) / 1_000_000  # ms
    df["Deserialization Time ROS"] = (df["End Deserialize ROS"] - df["Start Deserialize ROS"]) / 1_000_000  # ms
    df["ROS Processing Time"] = (df["Start Serialize ROS"] - df["End Deserialize ROS"]) / 1_000_000  # ms
    df["Serialization Time ROS"] = (df["End Serialize ROS"] - df["Start Serialize ROS"]) / 1_000_000  # ms
    df["Send to Py Delay"] = (df["Start Deserialize Py"] - df["End Serialize ROS"]) / 1_000_000  # ms
    df["Deserialization Time Py"] = (df["End Deserialize Py"] - df["Start Deserialize Py"]) / 1_000_000  # ms
    df["Reception Delay"] = (df["Received Time"] - df["End Deserialize Py"]) / 1_000_000  # ms
    df["Total Transmission Time"] = (df["Received Time"] - df["Sent Time"]) / 1_000_000  # Full cycle
    
    return df

df = compute_timestamps(df, f'{base_path}_1')
df_2 = compute_timestamps(df_2, f'{base_path}_2')
df_3 = compute_timestamps(df_3, f'{base_path}_3')
df = compute_delays(df)
df_2 = compute_delays(df_2)
df_3 = compute_delays(df_3)

df = pd.concat([df, df_2, df_3]).reset_index(drop=True)

# Compute statistics
def compute_statistics_ros2api(df): #.mean(), .median(), .std(), .max(), .quantile(0.95), .quantile(0.99)
    stats = {
        "Mean Serialization Time (Python)": df["Serialization Time Py"].mean(),
        "Mean Send to ROS Time": df["Send to ROS Delay"].mean(),
        "Mean Deserialization Time (ROS)": df["Deserialization Time ROS"].mean(),
        "Mean ROS Processing Time": df["ROS Processing Time"].mean(),
        "Mean Serialization Time (ROS)": df["Serialization Time ROS"].mean(),
        "Mean Send to Py Time": df["Send to Py Delay"].mean(),
        "Mean Deserialization Time (Python)": df["Deserialization Time Py"].mean(),
        "Mean Total Transmission Time": df["Total Transmission Time"].mean(),
        
        "Median Serialization Time (Python)": df["Serialization Time Py"].median(),
        "Median Send to ROS Time": df["Send to ROS Delay"].median(),
        "Median Deserialization Time (ROS)": df["Deserialization Time ROS"].median(),
        "Median ROS Processing Time": df["ROS Processing Time"].median(),
        "Median Serialization Time (ROS)": df["Serialization Time ROS"].median(),
        "Median Send to Py Time": df["Send to Py Delay"].median(),
        "Median Deserialization Time (Python)": df["Deserialization Time Py"].median(),
        "Median Total Transmission Time": df["Total Transmission Time"].median(),
        
        "Standard Deviation Serialization Time (Python)": df["Serialization Time Py"].std(),
        "Standard Deviation Send to ROS Time": df["Send to ROS Delay"].std(),
        "Standard Deviation Deserialization Time (ROS)": df["Deserialization Time ROS"].std(),
        "Standard Deviation ROS Processing Time": df["ROS Processing Time"].std(),
        "Standard Deviation Serialization Time (ROS)": df["Serialization Time ROS"].std(),
        "Standard Deviation Send to Py Time": df["Send to Py Delay"].std(),
        "Standard Deviation Deserialization Time (Python)": df["Deserialization Time Py"].std(),
        "Standard Deviation Total Transmission Time": df["Total Transmission Time"].std(),
        
        "Max Serialization Time (Python)": df["Serialization Time Py"].max(),
        "Max Send to ROS Time": df["Send to ROS Delay"].max(),
        "Max Deserialization Time (ROS)": df["Deserialization Time ROS"].max(),
        "Max ROS Processing Time": df["ROS Processing Time"].max(),
        "Max Serialization Time (ROS)": df["Serialization Time ROS"].max(),
        "Max Send to Py Time": df["Send to Py Delay"].max(),
        "Max Deserialization Time (Python)": df["Deserialization Time Py"].max(),
        "Max Total Transmission Time": df["Total Transmission Time"].max(),
        
        "95th Percentile Serialization Time (Python)": df["Serialization Time Py"].quantile(0.95),
        "95th Percentile Send to ROS Time": df["Send to ROS Delay"].quantile(0.95),
        "95th Percentile Deserialization Time (ROS)": df["Deserialization Time ROS"].quantile(0.95),
        "95th Percentile ROS Processing Time": df["ROS Processing Time"].quantile(0.95),
        "95th Percentile Serialization Time (ROS)": df["Serialization Time ROS"].quantile(0.95),
        "95th Percentile Send to Py Time": df["Send to Py Delay"].quantile(0.95),
        "95th Percentile Deserialization Time (Python)": df["Deserialization Time Py"].quantile(0.95),
        "95th Percentile Total Transmission Time": df["Total Transmission Time"].quantile(0.95),
        
        "99th Percentile Serialization Time (Python)": df["Serialization Time Py"].quantile(0.99),
        "99th Percentile Send to ROS Time": df["Send to ROS Delay"].quantile(0.99),
        "99th Percentile Deserialization Time (ROS)": df["Deserialization Time ROS"].quantile(0.99),
        "99th Percentile ROS Processing Time": df["ROS Processing Time"].quantile(0.99),
        "99th Percentile Serialization Time (ROS)": df["Serialization Time ROS"].quantile(0.99),
        "99th Percentile Send to Py Time": df["Send to Py Delay"].quantile(0.99),
        "99th Percentile Deserialization Time (Python)": df["Deserialization Time Py"].quantile(0.99),
        "99th Percentile Total Transmission Time": df["Total Transmission Time"].quantile(0.99)
    }
    
    for key, value in stats.items():
        print(f"{key}: {value:.3f} ms")
        
def compute_statistics_rosbridge(df):
    stats = {
        "Mean Total Transmission Time": df["Total Transmission Time"].mean(),
        "Median Total Transmission Time": df["Total Transmission Time"].median(),
        "Standard Deviation Total Transmission Time": df["Total Transmission Time"].std(),
        "Max Total Transmission Time": df["Total Transmission Time"].max(),
        "95th Percentile Total Transmission Time": df["Total Transmission Time"].quantile(0.95),
        "99th Percentile Total Transmission Time": df["Total Transmission Time"].quantile(0.99),
        "Max Total Time, with first Message Removed": df["Total Transmission Time"][5:].max()
    }
    
    for key, value in stats.items():
        print(f"{key}: {value:.3f} ms")
    
def plot_normal_histogram(df, bins=100):
    plt.figure(figsize=(10, 6))
        
    plt.hist(df["Total Transmission Time"], bins=bins, alpha=0.7, edgecolor='gray')
    csfont = {'fontname':'Times New Roman', 'fontsize': 14}

    plt.xlabel("Delay (ms)",  **csfont)
    plt.ylabel("Frequency", **csfont)
    if run.startswith("rosbridge"):
        plt.title("Histogram: rosbridge",  **csfont)
    if run.startswith("uds"):
        plt.title("Histogram: Unix Domain Socket",  **csfont)
    if run.startswith("tcp"):
        plt.title("Histogram: Transmission Control Protocol",  **csfont)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.show()

# Plot stacked bar chart (Average delay contributions)
def plot_average_bar_chart(df):
    csfont = {'fontname':'Times New Roman', 'fontsize': 14}
    categories = [
        "Transmission Delay", "Serialization Time (Python)", "Send to ROS",
        "Deserialization Time (ROS)", "ROS Processing Time", "Serialization Time (ROS)",
        "Send to Python", "Deserialization Time (Python)", "Reception Delay"
    ]
    
    column_names = [
        "Transmission Delay", "Serialization Time Py", "Send to ROS Delay",
        "Deserialization Time ROS", "ROS Processing Time", "Serialization Time ROS",
        "Send to Py Delay", "Deserialization Time Py", "Reception Delay"
    ]
    averages = [df[col].mean() for col in column_names]

    plt.figure(figsize=(8, 6))
    plt.barh(categories, averages, alpha=0.7)

    plt.xlabel("Average Time (ms)", **csfont)
    if run.startswith("rosbridge"):
        plt.title("Average Delay rosbridge", **csfont)
    if run.startswith("uds"):
        plt.title("Average Delay Unix Domain Socket", **csfont)
    if run.startswith("tcp"):
        plt.title("Average Delay TCP", **csfont)
    plt.grid(axis="x", linestyle="--", alpha=0.6)
    plt.show()

def plot_single_stacked_bar(df):
    categories = [
        "Transmission Delay", "Serialization Time Py", "Send to ROS Delay",
        "Deserialization Time ROS", "ROS Processing Time", "Serialization Time ROS",
        "Send to Py Delay", "Deserialization Time Py", "Reception Delay"
    ]
    
    # Get mean values for each category
    averages = [df[col].mean() for col in categories]
    
    # Create a colormap
    colors = plt.cm.viridis(np.linspace(0, 1, len(categories)))
    
    # Create a figure with appropriate size
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot the stacked bar
    left = 0
    for i, (value, category, color) in enumerate(zip(averages, categories, colors)):
        ax.barh(0, value, left=left, height=0.5, label=category, color=color)
        
        # Add text labels in the middle of each segment
        # Only add if the segment is wide enough
        if value > sum(averages) * 0.03:  # Only label segments that are at least 3% of total
            ax.text(left + value/2, 0, f"{category}\n{value:.2f}ms", 
                   ha='center', va='center', color='white', fontweight='bold')
        
        left += value
    
    # Remove y-axis and set labels
    ax.set_yticks([])
    ax.set_xlabel("Time (ms)")
    ax.set_title("End-to-End Delay Breakdown")
    
    # Add total time as text
    total_time = sum(averages)
    ax.text(total_time + 0.1, 0, f"Total: {total_time:.2f}ms", va='center')
    
    # Add a legend below the chart
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
    
    plt.tight_layout()
    plt.grid(axis="x", linestyle="--", alpha=0.3)
    plt.show()

# Plot delay trend (Line Graph)
def plot_delay_trend(df, column="Total Transmission Time"):
    plt.figure(figsize=(12, 6))
    plt.plot(np.array(df["ID"]), np.array(df[column]), linestyle="-", marker=".", alpha=0.5)
    plt.xlabel("Message ID (Ordered by Time)")
    plt.ylabel("Delay (ms)")
    plt.title(f"Trend of {column} Over Time")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

# Plot smoothed delay trend
def plot_smoothed_trend(df, column="Total Transmission Time", window_size=1000):
    smoothed_values = df[column].rolling(window=window_size).mean().to_numpy()

    plt.figure(figsize=(12, 6))
    plt.plot(df["ID"].to_numpy(), smoothed_values, linestyle="-", color="red", alpha=0.8, label="Smoothed Trend")
    
    plt.xlabel("Message ID (Ordered by Time)")
    plt.ylabel("Delay (ms)")
    plt.title(f"Smoothed Trend of {column} (Window={window_size})")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()

# ---- Run Functions ----
if not run.startswith("rosbridge"):
    #compute_statistics_ros2api(df) 
    plot_normal_histogram(df)
    plot_single_stacked_bar(df)     
    plot_average_bar_chart(df)
    plot_delay_trend(df) # Possible with rosbridge data
    plot_smoothed_trend(df)
else:
    compute_statistics_rosbridge(df)
    plot_normal_histogram(df)
    plot_delay_trend(df)
    plot_smoothed_trend(df)
