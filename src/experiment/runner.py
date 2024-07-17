import sys
import threading
import docker
import docker.types
import os
import time
import json
import shutil
import logging
from misc.config import load_configuration
from processes_capture import ProcessesCapture
from misc.util import get_display_name_tagged, create_directory

class Runner:

    def __init__(self, mode, config_path):
        self.config = load_configuration(config_path)
        self.mode = mode
        self.client = docker.from_env()
        self.pc = ProcessesCapture()
        self.curr_dir_prefix = ""
        self.active_containers = set()

    def run(self):
        try:
            images = []
            for image in self.config['images']:
                logging.info("Pulling image %s", image)
                images.append(self.client.images.pull(image))
            
            self.setup()

            if 'experiment_warmup' in self.config['procedure']:
                self.warmup()

            for i in range(self.config['procedure']['external_repetitions']):
                for image in images:
                    self.curr_dir_prefix = f"/{i}"
                    self.run_variation(image)
                    # Cooldown period
                    if 'cooldown' in self.config['procedure']:
                        time.sleep(self.config['procedure']['cooldown'])
        
        except docker.errors.ImageNotFound as e:
            logging.error(f"Docker image not found: {e}")
        except docker.errors.APIError as e:
            logging.error(f"Docker API error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in run method: {e}")
        finally:
            self.cleanup_all_containers()

    def run_variation(self, image):
        scaph = None
        try: 
            logging.info("Running variation %s", image.tags[0])

            image_name = image.tags[0]
            display_name = get_display_name_tagged(image_name)
            directory = display_name + self.curr_dir_prefix
            create_directory(self.config['out'] + "/" + directory)

            self.pc.start_tracing(f"{self.config['out']}/{directory}/ptrace.txt")

            volumes = {self.config['out']:{'bind':'/home', 'mode':'rw'}}
            
            scaph = self.start_scaphandre(directory)
            self.active_containers.add(scaph)
            if 'scaph_warmup' in self.config['procedure']:
                time.sleep(self.config['procedure']['scaph_warmup'])

            start_time = time.time()
            
            env = {"REPETITIONS":self.config['procedure']['internal_repetitions'], "TS_PATH":f'/home/{directory}/timesheet.json'}
            
            try:
                run_thread = threading.Thread(target=self.run_container, args=(image, display_name, volumes, env))
                run_thread.start()

                container_pid = self.get_container_pid_with_retry(display_name)
                if container_pid:
                    logging.info("Container PID: %d", container_pid)
                else:
                    logging.error("Failed to retrieve the container PID")

                run_thread.join()

            except Exception as e:
                logging.error(f"Error in container thread for {display_name}: {e}")

            end_time = time.time()
            self.timestamp(display_name, start_time, end_time, directory)

            self.cleanup_container(scaph)

            self.pc.stop_tracing()
            self.write_pid(directory, container_pid)
            logging.info("Done with %s", image.tags[0])

        except Exception as e:
            logging.error(f"Error when running variation {image.tags[0]}: {e}")
            self.pc.stop_tracing()
            if scaph:
                self.cleanup_container(scaph)

    def run_container(self, image, display_name, volumes, env):
        container = None
        try: 
            container = self.client.containers.run(image, auto_remove=True, name=display_name, volumes=volumes, environment=env, detach=True)
            self.active_containers.add(container)
            container.wait()
        except docker.errors.APIError as e:
            logging.error(f"Docker API error when running container {display_name}: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error when running container {display_name}: {e}")
            raise
        finally:
            if container:
                self.cleanup_container(container)

    def write_pid(self, directory, pid):
        file_path = self.config['out'] + f'/{directory}/rpid.txt'
        with open(file_path, 'w') as file:
            file.write(str(pid))

    def get_container_pid_with_retry(self, display_name, max_retries=5):
        retry_delay = 0.25 
        for attempt in range(max_retries):
            try:
                container = self.client.containers.get(display_name)
                inspection = self.client.api.inspect_container(container.id)
                return inspection['State']['Pid']
            except docker.errors.NotFound:
                logging.warning("Attempt %d failed, retrying in %f seconds...", attempt + 1, retry_delay)
                time.sleep(retry_delay)
                retry_delay *= 2
        return None

    def get_container_pid(self, container):
        inspection = self.client.api.inspect_container(container.id)
        return inspection['State']['Pid']

    def timestamp(self, event_id, start_time, end_time, directory):
        duration_seconds = end_time - start_time

        event_entry =  {
            "name": event_id,
            "start": start_time,
            "end": end_time,
            "duration": duration_seconds
        }
        
        events = []
        file_path = self.config['out'] + f'/{directory}/timesheet.json'
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                try:
                    events = json.load(file)
                except json.JSONDecodeError:
                    events = []

        events.append(event_entry)

        with open(file_path, 'w') as file:
            json.dump(events, file, indent=4)

    def setup(self):
        self.client.images.pull('philippsommer27/scaphandre', platform='linux/amd64')

        # Docker configuration for scaphandre
        self.volumes = {
            '/proc':{'bind':'/proc', 'mode': 'rw'},
            '/sys/class/powercap':{'bind':'/sys/class/powercap', 'mode':'rw'}
        }
        self.ports = {'8080':'8080'}

        # Clear output directory
        if os.path.exists(self.config['out']):
            for item in os.listdir(self.config['out']):
                item_path = os.path.join(self.config['out'], item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        
    def start_scaphandre(self, directory):
        self.volumes[self.config['out']] = {'bind':'/home', 'mode':'rw'}
        return self.client.containers.run('philippsommer27/scaphandre',
                                            f"json -s 0 --step-nano {self.config['procedure']['freq']} -f /home/{directory}/power.json", 
                                            volumes=self.volumes,
                                            privileged=True,
                                            detach=True,
                                            name='scaphandre')
    
    def warmup(self): 
        warmup_time = self.config['procedure']['warmup']
        start_time = time.time()
        end_time = start_time + warmup_time
        logging.info(f"Warming up for {warmup_time} seconds...")

        while time.time() < end_time:
            _ = [x**2 for x in range(1000)]

    def cleanup_container(self, container):
        try:
            container.stop()
            container.remove()
            self.active_containers.remove(container)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logging.error(f"Error cleaning up container {container.name}: {e}")
    
    def cleanup_all_containers(self):
        for container in list(self.active_containers):
            self.cleanup_container(container)
    
def signal_handler(*_):
    logging.info("Received termination signal. Cleaning up...")
    runner.cleanup_all_containers()
    runner.pc.stop_tracing()
    sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
    runner = Runner("","test.yaml")
    runner.run()
    