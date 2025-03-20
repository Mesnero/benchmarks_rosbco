import pandas as pd
import os
import glob

def normalize_and_split_csv(file_path):
    """
    Process a CSV file with timestamps and normalize them by subtracting the first timestamp values.
    Always splits the file in half to manage file size.
    """
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)
    
    if df.empty:
        print(f"No data in {file_path}")
        return []
    
    # Get the base values from the first row
    base_sent_time = df['Sent Time'].iloc[0]
    base_received_time = df['Received Time'].iloc[0]
    
    # Normalize all timestamps by subtracting the base values
    df['Sent Time'] = df['Sent Time'] - base_sent_time
    df['Received Time'] = df['Received Time'] - base_received_time
    
    # Create base file path for the normalized data
    dir_name, file_name = os.path.split(file_path)
    base_name, ext = os.path.splitext(file_name)
    
    # Always split the file in half
    split_point = len(df) // 2
    
    # First half
    part1_df = df.iloc[:split_point].copy()
    part1_path = os.path.join(dir_name, f"{base_name}_normalized_part1{ext}")
    part1_df.to_csv(part1_path, index=False)
    part1_size_mb = os.path.getsize(part1_path) / (1024 * 1024)
    
    # Second half
    part2_df = df.iloc[split_point:].copy()
    part2_path = os.path.join(dir_name, f"{base_name}_normalized_part2{ext}")
    part2_df.to_csv(part2_path, index=False)
    part2_size_mb = os.path.getsize(part2_path) / (1024 * 1024)
    
    print(f"Processed {file_path}")
    print(f"  Subtracted sent time: {base_sent_time}")
    print(f"  Subtracted received time: {base_received_time}")
    print(f"  Split into two parts:")
    print(f"    Part 1: {part1_path} ({part1_size_mb:.2f} MB)")
    print(f"    Part 2: {part2_path} ({part2_size_mb:.2f} MB)")
    
    return [part1_path, part2_path]

def main():
    # Find all arrived_messages.csv files in benchmark/data subdirectories that include "limit"
    csv_files = []
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'data')):
        if 'limit' in os.path.basename(root):
            for file in files:
                if file == 'arrived_messages.csv':
                    csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        print("No CSV files found in 'limit' directories!")
        return
    
    print(f"Found {len(csv_files)} CSV files to process in limit directories")
    
    normalized_files = []
    for file_path in csv_files:
        new_files = normalize_and_split_csv(file_path)
        normalized_files.extend(new_files)
    
    print(f"All files processed successfully. Created {len(normalized_files)} normalized files.")

if __name__ == "__main__":
    main()