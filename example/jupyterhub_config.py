from os import getenv
import socket
from traitlets.config import get_config


def get_host_ip():
    """
    Get the IP to connect to the host

    If you're using Podman 5+ the default IP will not work, set HOST_IP
    a non-default IP:
    https://blog.podman.io/2024/03/podman-5-0-breaking-changes-in-detail/
    """
    host_ip = getenv("HOST_IP")
    if not host_ip:
        # IP associated with the default route https://stackoverflow.com/a/28950776
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            host_ip = s.getsockname()[0]
    print(f"Host IP: {host_ip}")
    return host_ip


c = get_config()

c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.hub_connect_ip = get_host_ip()
c.JupyterHub.spawner_class = "podmancli"

c.PodmanCLISpawner.image = "quay.io/jupyter/base-notebook:latest"
c.PodmanCLISpawner.remove = True
