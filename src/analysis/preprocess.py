import json

def read(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()
    return json.loads(content)

def read_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def write_json(file_path, content):
    with open(file_path, 'w') as file:
        json.dump(content, file, indent=4)

def prune_edges(content, timesheet, event_name, buffer=0):
    print("pruning edges")
    event = next((event for event in timesheet if event['name'] == event_name), None)
    start = event['start'] - buffer
    end = event['end'] + buffer

    start_index = closest_index(content, start)
    end_index = closest_index(content, end, False)

    return content[start_index:end_index]

def closest_index(content, time, ascending=True):
    print("finding closest index")

    if ascending:
        if content[0]['host']['timestamp'] > time:
            print("time is before first entry")
            return -1
        index = 0
        current = content[index]['host']['timestamp']

        while current < time:
            index += 1
            current = content[index]['host']['timestamp']
    else:
        if content[-1]['host']['timestamp'] < time:
            print("time is after last entry")
            return -1
        index = len(content) - 1
        current = content[index]['host']['timestamp']

        while current > time:
            index -= 1
            current = content[index]['host']['timestamp']

    return index

def preprocess_scaphandre(filepath, timesheet_path, marker):
    content = read(filepath)

    timesheet = read_json(timesheet_path)
    corrected_content = prune_edges(content, timesheet, marker, 1)

    write_json(filepath, corrected_content)
    return corrected_content

if __name__ == '__main__':
    filepath = 'out/ce-t3-0.json'
    timesheet_path = 'out/ce-t3-0_t.json'
    preprocess_scaphandre(filepath, timesheet_path, "ce-t3-0/block")