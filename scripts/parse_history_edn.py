import pandas as pd
import re
import os

def parse_edn_file(file_path, output_path):
    def parse_edn_line(line):
        line = line.strip().replace(':', '').replace('[', '').replace(']', '').replace(',', '')
        pattern = re.findall(r'(\w+) ([^\s}]+)', line)
        return {key: value for key, value in pattern}

    with open(file_path, 'r') as file:
        content = file.readlines()

    parsed_data = [parse_edn_line(line) for line in content]
    df = pd.DataFrame(parsed_data)

    # Clean and preprocess the data
    relevant_columns = ['index', 'time', 'type', 'process', 'f', 'value', 'error']
    df_cleaned = df[relevant_columns].copy()  # Explicit copy to avoid warnings
    df_cleaned.loc[:, 'index'] = pd.to_numeric(df_cleaned['index'], errors='coerce')
    df_cleaned.loc[:, 'time'] = pd.to_numeric(df_cleaned['time'], errors='coerce')
    df_cleaned.loc[:, 'process'] = pd.to_numeric(df_cleaned['process'], errors='coerce')

    # Convert nanoseconds to seconds for interpretability
    df_cleaned.loc[:, 'time_seconds'] = df_cleaned['time'] / 1e9
    df_cleaned.loc[:, 'time_diff_seconds'] = df_cleaned['time_seconds'].diff()

    # Save the result to the output path
    output_file = os.path.join(output_path, "parsed_history.csv")
    df_cleaned.to_csv(output_file, index=False)
    print(f"Parsed data saved to {output_file}")

# Paths
file_path = '/Users/ericstine/projects/etcd_rust/results/history.edn'  # Path to the .edn file
output_path = '/Users/ericstine/projects/etcd_rust/results'  # Path to the results folder

# Parse the file
parse_edn_file(file_path, output_path)
