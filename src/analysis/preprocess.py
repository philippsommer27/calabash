import sys
from typing import List, Dict, Any
from misc.util import read_json, write_json
import logging

def prune_edges(content: List[Dict[str, Any]], timesheet: List[Dict[str, Any]], event_name: str, buffer: float) -> List[Dict[str, Any]]:
    event = next((event for event in timesheet if event['name'] == event_name), None)
    if not event:
        logging.error(f"No event named '{event_name}' found in timesheet")
        return content

    start = event['start'] - buffer
    end = event['end'] + buffer

    start_index = closest_index(content, start)
    end_index = closest_index(content, end, ascending=False)

    return content[start_index:end_index]

def closest_index(content: List[Dict[str, Any]], time: float, ascending: bool = True) -> int:
    if ascending:
        return find_closest_index_ascending(content, time)
    else:
        return find_closest_index_descending(content, time)

def find_closest_index_ascending(content: List[Dict[str, Any]], time: float) -> int:
    if content[0]['host']['timestamp'] > time:
        raise ValueError(f"First entry {content[0]['host']['timestamp']} is after time {time}")

    index = 0
    while content[index]['host']['timestamp'] < time:
        index += 1
    return index

def find_closest_index_descending(content: List[Dict[str, Any]], time: float) -> int:
    if content[-1]['host']['timestamp'] < time:
        raise ValueError(f"Last entry {content[-1]['host']['timestamp']} is before time {time}")

    index = len(content) - 1
    while content[index]['host']['timestamp'] > time:
        index -= 1
    return index

def preprocess_scaphandre(filepath: str, output: str, timesheet_path: str, prune_mark: str = "block", prune_buffer: float = 0) -> List[Dict[str, Any]]:
    try:
        content = read_json(filepath)
        timesheet = read_json(timesheet_path)
        corrected_content = prune_edges(content, timesheet, prune_mark, prune_buffer)
        write_json(output, corrected_content)
        return corrected_content
    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        sys.exit(1)