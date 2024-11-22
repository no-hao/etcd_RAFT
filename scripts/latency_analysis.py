import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the parsed data
file_path = '/Users/ericstine/projects/etcd_rust/results/parsed_history.csv'
parsed_data = pd.read_csv(file_path)

# Convert necessary columns to numeric
parsed_data['time_seconds'] = pd.to_numeric(parsed_data['time_seconds'], errors='coerce')
parsed_data['time_diff_seconds'] = pd.to_numeric(parsed_data['time_diff_seconds'], errors='coerce')
parsed_data['process'] = pd.to_numeric(parsed_data['process'], errors='coerce')

# Scatter Plot: Latency by Event Type
plt.figure(figsize=(12, 6))
sns.boxplot(data=parsed_data, x='type', y='time_diff_seconds', palette='Set2')
plt.title('Latency (Time Differences) by Event Type')
plt.xlabel('Event Type')
plt.ylabel('Latency (seconds)')
plt.show()

# Scatter Plot: Latency vs Process
plt.figure(figsize=(12, 6))
plt.scatter(parsed_data['process'], parsed_data['time_diff_seconds'], alpha=0.5, color='blue')
plt.axhline(parsed_data['time_diff_seconds'].mean(), color='red', linestyle='--', label='Mean Latency')
plt.title('Latency by Process')
plt.xlabel('Process')
plt.ylabel('Latency (seconds)')
plt.legend()
plt.show()

# Bar Chart: Average Latency per Process
average_latency_per_process = parsed_data.groupby('process')['time_diff_seconds'].mean().dropna()
plt.figure(figsize=(12, 6))
average_latency_per_process.plot(kind='bar', color='green')
plt.title('Average Latency by Process')
plt.xlabel('Process')
plt.ylabel('Average Latency (seconds)')
plt.show()

# Line Plot: Latency Over Time
plt.figure(figsize=(12, 6))
plt.plot(parsed_data['time_seconds'], parsed_data['time_diff_seconds'], label='Latency (seconds)', color='purple', alpha=0.7)
plt.title('Latency Over Time')
plt.xlabel('Time (seconds)')
plt.ylabel('Latency (seconds)')
plt.legend()
plt.show()

# Heatmap: Latency Distribution by Process and Event Type
heatmap_data = parsed_data.pivot_table(index='process', columns='type', values='time_diff_seconds', aggfunc="mean").fillna(0)
plt.figure(figsize=(12, 6))
sns.heatmap(heatmap_data, cmap='coolwarm', annot=False)
plt.title('Latency Heatmap: Process vs Event Type')
plt.xlabel('Event Type')
plt.ylabel('Process')
plt.show()

# Highlight High-Latency Events
high_latency_threshold = parsed_data['time_diff_seconds'].quantile(0.95)
outliers = parsed_data[parsed_data['time_diff_seconds'] > high_latency_threshold]

plt.figure(figsize=(12, 6))
sns.scatterplot(data=outliers, x='time_seconds', y='time_diff_seconds', hue='type', palette='Set1')
plt.title('High-Latency Events (95th Percentile)')
plt.xlabel('Time (seconds)')
plt.ylabel('Latency (seconds)')
plt.legend(title='Event Type')
plt.show()
