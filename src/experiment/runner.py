import docker
import docker.types
import os
import time
import json
from config import load_configuration

def run(mode, config_path):
    config = load_configuration(config_path)

    client = docker.from_env()
    
    images = []
    for image in config['images']:
        images.append(client.images.pull(image))

    containers = setup(mode, config['procedure']['freq'], config['out'])

    for image in images:
        run_variation(image, config['out'])
        # Cooldown period
        time.sleep(config['procedure']['cooldown'])

    cleanup(containers)

def run_variation(image, out):
    image_name = image.tags[0]
    display_name = image_name[image_name.find('/')+1:image_name.find(':')]

    client = docker.from_env()
    start_time = time.time()
    container = client.containers.run(image, auto_remove=True, name=display_name)
    end_time = time.time()

    timestamp(out, display_name, start_time, end_time)

    return container

def timestamp(out, event_id, start_time, end_time):
    duration_seconds = end_time - start_time

    event_entry = {
        event_id: {
            "start": start_time,
            "end": end_time,
            "duration": duration_seconds
        }
    }
    
    events = []
    file_path = out + '/timesheet.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                events = json.load(file)
            except json.JSONDecodeError:
                events = []

    events.append(event_entry)

    with open(file_path, 'w') as file:
        json.dump(events, file, indent=4)

def setup(mode, freq, data_path=''):
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
    
    if (mode == "prometheus"):
            # Set up volume for prometheus data
        volume_name = "promdata-scaphandre"
        client.volumes.create(name=volume_name)
        prom_container = setup_prometheus(network_name, volume_name)
        grafana_container = setup_grafana(network_name)
        scaphandre_container = client.containers.run('hubblo/scaphandre', 
                              'prometheus', 
                              volumes=volumes, 
                              ports=ports,
                              privileged=True,
                              network=network_name,
                              detach=True)
        
        return (prom_container, grafana_container, scaphandre_container, network_name)

    else:
        volumes[data_path] = {'bind':'/home', 'mode':'rw'}
        return (client.containers.run('hubblo/scaphandre', f'json -s 0 --step-nano {freq} -f /home/output.json', 
                                      volumes=volumes, 
                                      detach=True,
                                      name='scaphandre'))

def setup_grafana(network_name):
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

def setup_prometheus(network_name, volume_name):
    client = docker.from_env()

    client.images.build(path="./src/docker/prom/", rm=True, tag='cb_prometheus')

    return client.containers.run('cb_prometheus', 
                          ports={'9090':'9090'}, 
                          detach=True, 
                          network=network_name,
                          volumes=[f'{volume_name}:/prometheus'],
                          name='cb_prometheus'
                          )

def cleanup(containers):
    for container in containers:
        try: 
            container.stop()
            container.remove()
        except ValueError:
            print("Error during cleanup...")
    
if __name__ == "__main__":
    run("","test.yaml")
    