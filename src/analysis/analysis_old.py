import json
import matplotlib.pyplot as plt
from datetime import datetime
from preprocess import correct_json

file_path = 'out/ce-t3-0.json'
file_path_fixed = 'out/corrected_output.json'

def read_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_host_consumption(json_data):
    timestamps = []
    consumptions = []
    for entry in json_data:
        host = entry['host']
        readable_timestamp = datetime.fromtimestamp(host['timestamp'])
        timestamps.append(readable_timestamp)
        consumptions.append(host['consumption'])
    return timestamps, consumptions

def plot_data(timestamps, consumptions):
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, consumptions, marker='o', linestyle='-')
    plt.title('Host Consumption Over Time')
    plt.xlabel('Time')
    plt.ylabel('Consumption')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('out/host_consumption_plot.png', format='png')
    plt.close()

def analyze(path):
    json_data = read_json_data(file_path_fixed)
    timestamps, consumptions = extract_host_consumption(json_data)
    plot_data(timestamps, consumptions)

if __name__ == '__main__':
    correct_json(file_path)
    analyze(file_path_fixed)
