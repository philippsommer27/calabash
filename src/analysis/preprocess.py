from misc.util import read_json, write_json
import logging

def prune_edges(content, timesheet, event_name, buffer):
    logging.info("Pruning edges")
    event = next((event for event in timesheet if event['name'] == event_name), None)
    start = event['start'] - buffer
    end = event['end'] + buffer

    start_index = closest_index(content, start)
    end_index = closest_index(content, end, False)

    return content[start_index:end_index]

def closest_index(content, time, ascending=True):
    if ascending:
        if content[0]['host']['timestamp'] > time:
            logging.error("First entry %d is after time %d", content[0]['host']['timestamp'], time)
            exit()
        index = 0
        current = content[index]['host']['timestamp']

        while current < time:
            index += 1
            current = content[index]['host']['timestamp']
    else:
        if content[-1]['host']['timestamp'] < time:
            logging.error("Last entry %d is before time %d", content[-1]['host']['timestamp'], time)
            exit()
        index = len(content) - 1
        current = content[index]['host']['timestamp']

        while current > time:
            index -= 1
            current = content[index]['host']['timestamp']

    return index

def preprocess_scaphandre(filepath, output, timesheet_path, prune_mark="block", prune_buffer=0):
    content = read_json(filepath)

    timesheet = read_json(timesheet_path)
    corrected_content = prune_edges(content, timesheet, prune_mark, prune_buffer)

    write_json(output, corrected_content)
    return corrected_content