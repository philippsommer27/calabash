import json
import matplotlib.pyplot as plt
from datetime import datetime
import re

file_path = 'out/corrected_output.json'

def read_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def filter_and_accumulate_consumption(json_data, regex_pattern):
    pattern = re.compile(regex_pattern)
    
    accumulated_data = {}

    for entry in json_data:
        timestamp = datetime.fromtimestamp(entry['host']['timestamp']).isoformat()

        if timestamp not in accumulated_data:
            accumulated_data[timestamp] = 0.0

        for consumer in entry['consumers']:
            if pattern.search(consumer['exe']) or pattern.search(consumer['cmdline']):
                accumulated_data[timestamp] += consumer['consumption']

    sorted_timestamps = sorted(accumulated_data.keys())
    sorted_consumptions = [accumulated_data[timestamp] for timestamp in sorted_timestamps]

    return sorted_timestamps, sorted_consumptions

def plot_data(timestamps, consumptions):
    timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, consumptions, marker='o', linestyle='-')
    plt.title('Accumulated Consumption Over Time')
    plt.xlabel('Time')
    plt.ylabel('Accumulated Consumption')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('out/regex_consumption.png', format='png')
    plt.close()

def main():
    regex_pattern = r'(?i).*java.*'
    json_data = read_json_data(file_path)
    timestamps, consumptions = filter_and_accumulate_consumption(json_data, regex_pattern)
    plot_data(timestamps, consumptions)

if __name__ == '__main__':
    main()
