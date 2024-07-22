import psutil
import time
import threading
import csv
import logging

def get_cpu_temp():
    sensors = psutil.sensors_temperatures()
    if not sensors:
        return None
    for name, entries in sensors.items():
        for entry in entries:
            if 'cpu' in entry.label.lower() or 'core' in entry.label.lower():
                return entry.current
    return None

def record_cpu_temp():
    global recording, cpu_temps
    start_time = time.time()
    while recording:
        temp = get_cpu_temp()
        if temp is not None:
            timestamp = time.time() - start_time
            cpu_temps.append((timestamp, temp))
            logging.debug("CPU Temperature: %.2f °C", temp)
        time.sleep(0.5)

def start_temp_recording():
    global recording, cpu_temps
    recording = True
    cpu_temps = []
    thread = threading.Thread(target=record_cpu_temp)
    thread.start()
    return thread

def stop_temp_recording(thread, filename="cpu_temps.csv"):
    global recording
    if recording:
        recording = False
        thread.join()

        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["time", "temperature_celcius"])
            writer.writerows(cpu_temps)
    else:
        logging.warning("Recording is not in progress.")
    
# Example usage
if __name__ == "__main__":
    recording_thread = start_temp_recording()
    input("Press Enter to stop recording...\n")
    stop_temp_recording(recording_thread)
