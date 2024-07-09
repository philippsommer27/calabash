from misc.util import read_json, read_file
import logging

def check(directory):
    power = read_json(f"{directory}/power.json")
    ptrace = read_file(f"{directory}/ptrace.txt")
    rpid = read_file(f"{directory}/rpid.txt")
    timesheet = read_json(f"{directory}/timesheet.json")

    return check_power(power) and check_ptrace(ptrace) and check_rpid(rpid) and check_timesheet(timesheet)

def check_timesheet(timesheet, freq=0.05):
    for element in timesheet:
        if element.get('name') == 'block':
            if element['duration'] < 2 * freq:
                logging.error("Block duration %d is too short", element['duration'])
                return False
            return True
    logging.error("No block event found")
    return False
            
def check_power(power):
    if len(power) < 1:
        logging.error("No power data found")
        return False
    return True

def check_ptrace(ptrace):
    if len(ptrace) < 1:
        logging.error("No ptrace data found")
        return False
    return True    

def check_rpid(rpid):
    if len(rpid) < 1:
        logging.error("No rpid data found")
        return False
    return True
