""" pytest config for podmanclispawner tests """

# https://github.com/jupyterhub/yarnspawner/blob/0.4.0/yarnspawner/tests/conftest.py
import pytest_asyncio

from jupyterhub.tests.mocking import MockHub
import os
import socket
from subprocess import check_output
import sys
from traitlets.config import Config

from podmanclispawner import PodmanCLISpawner


# make Hub connectable by default
MockHub.hub_ip = "0.0.0.0"


INTERNAL_HOST_LOOKUP = "host.containers.internal"


def _get_host_default_ip():
    """
    Get the IP to connect to the host hub
    """
    version = check_output(["podman", "version", "-f", "{{.Version}}"])
    major = int(version.decode().split(".", 1)[0])
    if major < 5:
        # IP associated with the default route https://stackoverflow.com/a/28950776
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]

    # Using the iface associated with the default route no longer works
    # with Podman 5+ as the container shares the host IP:
    # https://blog.podman.io/2024/03/podman-5-0-breaking-changes-in-detail/
    # Instead use the host.containers.internal host entry
    out = check_output(
        [
            "podman",
            "run",
            "--rm",
            "docker.io/library/busybox",
            "cat",
            "/etc/hosts",
        ]
    )
    for line in out.decode().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        ip, addresses = line.split(None, 1)
        if INTERNAL_HOST_LOOKUP in addresses.split():
            return ip
    raise RuntimeError(f"Failed to lookup {INTERNAL_HOST_LOOKUP} inside a container")


# https://docs.pytest.org/en/latest/example/parametrize.html#apply-indirect-on-particular-arguments
@pytest_asyncio.fixture()
async def app(request):
    """
    Mock a jupyterhub app for testing

    Takes a parameter indicating the name of the directory under examples
    """

    def abspath(f):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "examples",
            request.param,
            f,
        )

    c = Config()
    c.JupyterHub.spawner_class = PodmanCLISpawner
    c.PodmanCLISpawner.remove = True
    c.PodmanCLISpawner.start_timeout = 600
    c.JupyterHub.hub_connect_ip = _get_host_default_ip()

    mocked_app = MockHub.instance(config=c)

    await mocked_app.initialize([])
    await mocked_app.start()

    try:
        yield mocked_app
    finally:
        # disconnect logging during cleanup because pytest closes captured FDs
        # prematurely
        mocked_app.log.handlers = []
        MockHub.clear_instance()
        try:
            mocked_app.stop()
        except Exception as e:
            print("Error stopping Hub: %s" % e, file=sys.stderr)
