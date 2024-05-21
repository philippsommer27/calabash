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

    def run(self):
        client = docker.from_env()
        
        images = []
        for image in self.config['images']:
            images.append(client.images.pull(image))

        containers = self.setup()

        for image in images:
            self.run_variation(image)
            # Cooldown period
            time.sleep(self.config['procedure']['cooldown'])

        self.cleanup(containers)

    def run_variation(self, image):
        image_name = image.tags[0]
        display_name = image_name[image_name.find('/')+1:image_name.find(':')]

        client = docker.from_env()
        start_time = time.time()
        container = client.containers.run(image, auto_remove=True, name=display_name)
        end_time = time.time()

        self.timestamp(display_name, start_time, end_time)

        return container

    def timestamp(self, event_id, start_time, end_time):
        duration_seconds = end_time - start_time

        event_entry = {
            event_id: {
                "start": start_time,
                "end": end_time,
                "duration": duration_seconds
            }
        }
        
        events = []
        file_path = self.config['out'] + '/timesheet.json'
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
        client = docker.from_env()

        # Setup the network
        network_name = "main_network"
        ipam_pool = docker.types.IPAMPool(subnet='192.168.33.0/24', gateway='192.168.33.1')
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        client.networks.prune()
        client.networks.create(network_name, driver="bridge", ipam=ipam_config)

        client.images.pull('hubblo/scaphandre', platform='linux/amd64')

        # Docker configuration for scaphandre
        volumes = {
            '/proc':{'bind':'/proc', 'mode': 'rw'},
            '/sys/class/powercap':{'bind':'/sys/class/powercap', 'mode':'rw'}
        }
        ports = {'8080':'8080'}
        
        if (self.mode == "prometheus"):
                # Set up volume for prometheus data
            volume_name = "promdata-scaphandre"
            client.volumes.create(name=volume_name)
            prom_container = self.setup_prometheus(network_name, volume_name)
            grafana_container = self.setup_grafana(network_name)
            scaphandre_container = client.containers.run('hubblo/scaphandre', 
                                'prometheus', 
                                volumes=volumes, 
                                ports=ports,
                                privileged=True,
                                network=network_name,
                                detach=True)
            
            return (prom_container, grafana_container, scaphandre_container, network_name)

        else:
            volumes[self.config['out']] = {'bind':'/home', 'mode':'rw'}
            return [client.containers.run('hubblo/scaphandre', f"json -s 0 --step-nano {self.config['procedure']['freq']} -f /home/output.json", 
                                        volumes=volumes, 
                                        detach=True,
                                        name='scaphandre')]

    def setup_grafana(self, network_name):
        client = docker.from_env()
        
        client.images.build(path="./src/docker/grafana/",rm=True, tag='cb_grafana')
        environment = {
            'GF_SECURITY_ADMIN_PASSWORD':'secret',
            'GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH':'/var/lib/grafana/dashboards/default-dashboard.json'
        }
        absp = os.path.abspath('./src/docker/grafana/dashboards/')
        volumes = {absp:{
            'bind':'/var/lib/grafana/dashboards/',
            'mode':'ro'
            }}

        return client.containers.run(
            'cb_grafana', 
            ports={'3000':'3000'}, 
            detach=True, 
            network=network_name,
            environment=environment,
            volumes=volumes,
            name='cb_grafana'
        )

    def setup_prometheus(self, network_name, volume_name):
        client = docker.from_env()

        client.images.build(path="./src/docker/prom/", rm=True, tag='cb_prometheus')

        return client.containers.run('cb_prometheus', 
                            ports={'9090':'9090'}, 
                            detach=True, 
                            network=network_name,
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
    
if __name__ == "__main__":
    runner = Runner("","test.yaml")
    runner.run()
    