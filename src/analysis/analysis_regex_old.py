import json
import matplotlib.pyplot as plt
from datetime import datetime
import re

from preprocess import correct_json

file_path = 'out/ce-t3-1.json'
file_path_fixed = 'out/corrected_output.json'
events_file_path = 'out/ce-t3-1_t.json'

file_path1 = 'out/ce-t3-0.json'
file_path_fixed1 = 'out/corrected_output1.json'
events_file_path1 = 'out/ce-t3-0_t.json'

def read_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def read_event_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def filter_and_accumulate_consumption(json_data, regex_pattern):
    pattern = re.compile(regex_pattern)
    
    accumulated_data = {}

    for entry in json_data:
        timestamp = entry['host']['timestamp']

        if timestamp not in accumulated_data:
            accumulated_data[timestamp] = 0.0

        for consumer in entry['consumers']:
            if pattern.search(consumer['exe']) or pattern.search(consumer['cmdline']):
                accumulated_data[timestamp] += consumer['consumption']

    sorted_timestamps = sorted(accumulated_data.keys())
    shifted_timestamps = [timestamp - sorted_timestamps[0] for timestamp in sorted_timestamps]
    sorted_consumptions = [accumulated_data[timestamp] / 1000000 for timestamp in sorted_timestamps]

    return shifted_timestamps, sorted_consumptions

def plot_data(timestamps, consumptions, events, timestamps1, consumptions1, events1):

    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, consumptions, linestyle='-', color='g')
    plt.plot(timestamps1, consumptions1, linestyle='--', color='r')
    plt.xlabel('Time')
    plt.ylabel('Accumulated Consumption (Watt)')
    plt.grid(True)
    
    # # Plotting events
    # for event in events:
    #     for key, value in event.items():
    #         start_time = datetime.fromtimestamp(value['start'] / 1000 if value['start'] > 1e10 else value['start'])
    #         end_time = datetime.fromtimestamp(value['end'] / 1000 if value['end'] > 1e10 else value['end'])
    #         plt.axvline(x=start_time, color='r', linestyle='--', linewidth=1)
    #         plt.axvline(x=end_time, color='g', linestyle='--', linewidth=1)
    #         plt.text(start_time, max(consumptions), key + ' start', rotation=45, color='r')
    #         plt.text(end_time, max(consumptions), key + ' end', rotation=45, color='g')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('out/regex_consumption_with_events.png', format='png')
    plt.close()

def main():
    regex_pattern = r'.*java.*'
    json_data = read_json_data(file_path_fixed)
    json_data1 = read_json_data(file_path_fixed1)
    timestamps, consumptions = filter_and_accumulate_consumption(json_data, regex_pattern)
    timestamps1, consumptions1 = filter_and_accumulate_consumption(json_data1, regex_pattern)
    event_data = read_event_data(events_file_path)
    event_data1 = read_event_data(events_file_path1)
    plot_data(timestamps, consumptions, event_data, timestamps1, consumptions1, event_data1)

if __name__ == '__main__':
    correct_json(file_path, "")
    correct_json(file_path1, "1")
    main()
