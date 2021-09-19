# podmanclispawner

JupyterHub Podman Spawner.

This is a fork of https://github.com/gatoniel/podmanspawner without the dependencies on local system users.

## Overview

This is a simplified version of https://github.com/gatoniel/podmanspawner that runs Podman containers using the `podman` executable, but without tying the container to the local users.

For example, this means it can be used as a JupyterHub spawner for BinderHub, without the need for a daemon or privileged container engine.

### Technical

`subprocess.Popen` is used to make calls to Podman.
See also this [issue](https://github.com/jupyterhub/dockerspawner/issues/360) on
dockerspawner.

## Installation

Via pip:

    pip install git+https://github.com/manics/podmanclispawner

## JupyterHub configuration

```python
c.JupyterHub.spawner_class = 'podmancli'
```
