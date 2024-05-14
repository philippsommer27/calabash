import docker
import docker.types
import os
import time
from config import load_configuration

def run(mode, config_path):
    config = load_configuration(config_path)

    client = docker.from_env()
    
    base_image = client.images.pull(config['images'][0])
    green_image = client.images.pull(config['images'][1])

    containers = setup(mode, config['procedure']['freq'], config['out'])

    containers.append(client.containers.run(base_image, auto_remove=True))

    # Cooldown period
    time.sleep(config['procedure']['cooldown'])

    containers.append(client.containers.run(green_image, auto_remove=True))

    cleanup(containers)

def run_variation(image_name):
    client = docker.from_env()
    image = client.images.pull(image_name)
    return client.containers.run(image, auto_remove=True)

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
        return client.containers.run('hubblo/scaphandre', f'json -s 0 --step-nano {freq} -f /home/output.json', volumes=volumes, detach=True)

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
    run("","src/test.yaml")
    