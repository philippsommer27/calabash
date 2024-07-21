import datetime
import platform
import psutil

def get_metadata() -> dict:
    metadata = {
        "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Operating System": platform.system(),
        "OS Version": platform.version(),
        "OS Version Name": platform.freedesktop_os_release().get("VERSION_CODENAME"),
        "Kernel Version": platform.release(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "CPU Cores": psutil.cpu_count(logical=False),
        "Logical CPUs": psutil.cpu_count(logical=True),
        "Total RAM (GB)": round(psutil.virtual_memory().total / (1024**3), 2)
    }
    return metadata
