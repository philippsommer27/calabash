import docker
import docker.types
import os
import time
import json
from config import load_configuration

class Runner:
    def __init__(self, mode, config_path):
        self.config = load_configuration(config_path)
        self.mode = mode
        self.network_name = "main_network"
        self.client = docker.from_env()

    def run(self):        
        images = []
        for image in self.config['images']:
            images.append(self.client.images.pull(image))

        containers = self.setup()

        for image in images:
            self.run_variation(image)
            # Cooldown period
            time.sleep(self.config['procedure']['cooldown'])


    def run_variation(self, image):
        print(f"Running variation {image.tags[0]}")

        image_name = image.tags[0]
        display_name = image_name[image_name.find('/')+1:image_name.find(':')]

        volumes = {self.config['out']:{'bind':'/home', 'mode':'rw'}}
        
        scaph = self.start_scaphandre(display_name)

        start_time = time.time()
        self.client.containers.run(image, auto_remove=True, name=display_name, volumes=volumes)
        end_time = time.time()
        self.timestamp(display_name, start_time, end_time, display_name)

        scaph.stop()
        scaph.remove()

        print(f"Done with {image.tags[0]}")

    def timestamp(self, event_id, start_time, end_time, display_name):
        duration_seconds = end_time - start_time

        event_entry =  {
            "name": event_id,
            "start": start_time,
            "end": end_time,
            "duration": duration_seconds
        }
        
        events = []
        file_path = self.config['out'] + f'/{display_name}_t.json'
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
        # Setup the network
        self.client.networks.prune()
        ipam_pool = docker.types.IPAMPool(subnet='192.168.33.0/24', gateway='192.168.33.1')
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        self.client.networks.create(self.network_name, driver="bridge", ipam=ipam_config)

        self.client.images.pull('hubblo/scaphandre', platform='linux/amd64')

        # Docker configuration for scaphandre
        self.volumes = {
            '/proc':{'bind':'/proc', 'mode': 'rw'},
            '/sys/class/powercap':{'bind':'/sys/class/powercap', 'mode':'rw'}
        }
        self.ports = {'8080':'8080'}
        
    def start_prom_graf(self):
        # Set up volume for prometheus data
        volume_name = "promdata-scaphandre"
        self.client.volumes.create(name=volume_name)
        prom_container = self.setup_prometheus(volume_name)
        grafana_container = self.setup_grafana()
        scaphandre_container = self.client.containers.run('hubblo/scaphandre', 
                            'prometheus', 
                            volumes=self.volumes, 
                            ports=self.ports,
                            privileged=True,
                            network=self.network_name,
                            detach=True)
        
        return (prom_container, grafana_container, scaphandre_container)
        
    def start_scaphandre(self, display_name):
        self.volumes[self.config['out']] = {'bind':'/home', 'mode':'rw'}
        return self.client.containers.run('hubblo/scaphandre',
                                            f"json -s 0 --step-nano {self.config['procedure']['freq']} -f /home/{display_name}.json", 
                                            volumes=self.volumes, 
                                            detach=True,
                                            name='scaphandre')

    def setup_grafana(self):        
        self.client.images.build(path="./src/docker/grafana/",rm=True, tag='cb_grafana')
        environment = {
            'GF_SECURITY_ADMIN_PASSWORD':'secret',
            'GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH':'/var/lib/grafana/dashboards/default-dashboard.json'
        }
        absp = os.path.abspath('./src/docker/grafana/dashboards/')
        volumes = {absp:{
            'bind':'/var/lib/grafana/dashboards/',
            'mode':'ro'
            }}

        return self.client.containers.run(
            'cb_grafana', 
            ports={'3000':'3000'}, 
            detach=True, 
            network=self.network_name,
            environment=environment,
            volumes=volumes,
            name='cb_grafana'
        )

    def setup_prometheus(self, volume_name):
        self.client.images.build(path="./src/docker/prom/", rm=True, tag='cb_prometheus')

        return self.client.containers.run('cb_prometheus', 
                            ports={'9090':'9090'}, 
                            detach=True, 
                            network=self.network_name,
                            volumes=[f'{volume_name}:/prometheus'],
                            name='cb_prometheus'
                            )

    def cleanup(self, containers):
        for container in containers:
            try: 
                container.stop()
                container.remove()
            except ValueError:
                print("Error during cleanup...")

        self.client.networks.prune()
    
if __name__ == "__main__":
    runner = Runner("","test.yaml")
    runner.run()
    