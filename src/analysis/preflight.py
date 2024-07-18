from typing import List, Dict, Any
from misc.util import read_json, read_file
import logging

def check(directory: str) -> bool:
    power = read_json(f"{directory}/power.json")
    ptrace = read_file(f"{directory}/ptrace.txt")
    rpid = read_file(f"{directory}/rpid.txt")
    timesheet = read_json(f"{directory}/timesheet.json")

    return all([
        check_power(power),
        check_ptrace(ptrace),
        check_rpid(rpid),
        check_timesheet(timesheet)
    ])

def check_timesheet(timesheet: List[Dict[str, Any]], freq: float = 0.05) -> bool:
    for element in timesheet:
        if element.get('name') == 'block':
            if element['duration'] < 2 * freq:
                log_error("Block duration %f is too short", element['duration'])
                return False
            return True
    log_error("No block event found")
    return False

def check_power(power: List[Any]) -> bool:
    return check_non_empty_list(power, "power")

def check_ptrace(ptrace: List[Any]) -> bool:
    return check_non_empty_list(ptrace, "ptrace")

def check_rpid(rpid: str) -> bool:
    return check_non_empty_string(rpid, "rpid")

def check_non_empty_list(data: List[Any], data_type: str) -> bool:
    if len(data) < 1:
        log_error(f"No {data_type} data found")
        return False
    return True

def check_non_empty_string(data: str, data_type: str) -> bool:
    if len(data.strip()) < 1:
        log_error(f"No {data_type} data found")
        return False
    return True

def log_error(message: str, *args: Any) -> None:
    logging.error(message, *args)
