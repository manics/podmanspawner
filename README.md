# podmanclispawner

[![PyPI version](https://badge.fury.io/py/podmanclispawner.svg)](https://pypi.org/project/podmanclispawner/)
[![GitHub Workflow](https://github.com/manics/podmanclispawner/workflows/Build/badge.svg?branch=main&event=push)](https://github.com/manics/podmanclispawner/actions)

JupyterHub Podman Spawner.

This is a fork of https://github.com/gatoniel/podmanspawner without the dependencies on local system users.

## Overview

This is a simplified version of https://github.com/gatoniel/podmanspawner that runs Podman containers using the `podman` executable, but without tying the container to the local users.

For example, this means it can be used as a JupyterHub spawner for BinderHub, without the need for a daemon or privileged container engine.

### Technical

`subprocess` is used to make calls to the Podman executable.
See also this [issue](https://github.com/jupyterhub/dockerspawner/issues/360) on
dockerspawner.

## Installation

Install latest release:

    pip install podmanclispawner

Install latest development branch:

    pip install git+https://github.com/manics/podmanclispawner

## JupyterHub configuration

```python
c.JupyterHub.spawner_class = 'podmancli'
```

For a full example see [`example/jupyterhub_config.py`](example/jupyterhub_config.py):

    cd example
    jupyterhub -f jupyterhub_config.py
