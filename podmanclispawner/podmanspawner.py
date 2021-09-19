# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# copied from the jupyterhub.spawner.LocalProcessSpawner

import json
import os
from subprocess import Popen, PIPE
from traitlets import Bool
from traitlets import Dict
from traitlets import Integer
from traitlets import List
from traitlets import Unicode

from jupyterhub.spawner import Spawner


class PodmanCLISpawner(Spawner):
    """
    A Spawner that uses `subprocess.Popen` to start single-user servers as
    podman containers.
    Does not work on Windows.
    """

    popen_kwargs = Dict(
        help="""Extra keyword arguments to pass to Popen
        when spawning single-user servers.
        For example::
            popen_kwargs = dict(shell=True)
        """
    ).tag(config=True)

    cid = Unicode(
        allow_none=True,
        help="""
        The container id (cid) of the single-user server container spawned for current
        user.
        """,
    )

    image = Unicode(
        "docker.io/jupyterhub/singleuser",
        config=True,
        help="""The image to use for single-user servers.
        This image should have the same version of jupyterhub as
        the Hub itself installed.
        If the default command of the image does not launch
        jupyterhub-singleuser, set `c.Spawner.cmd` to
        launch jupyterhub-singleuser, e.g.
        Any of the jupyter docker-stacks should work without additional config,
        as long as the version of jupyterhub in the image is compatible.
        """,
    ).tag(config=True)

    pull_image_first = Bool(
        False,
        help="""Run podman pull image, before podman run to circumvent current
        transport problem.""",
    )

    pull_image = Unicode(
        allow_none=True,
        help="""When image should be pulled first, where to pull from?""",
    )

    standard_jupyter_port = Integer(
        8888,
        help="""The standard port, the Jupyter Notebook is listening in the
        container to.""",
    )

    https_proxy = Unicode(
        allow_none=True,
        help="""Is your server running behind a proxy? Podman needs to now, to
        pull images correctly.""",
    ).tag(config=True)

    podman_additional_cmds = List(
        default_value=[],
        help="""These commands are appended to the podman_base_cmd. They are
        then followed by the jupyter_base_cmd""",
    ).tag(config=True)

    jupyter_additional_cmds = List(
        default_value=[],
        help="""These commands are appended to the jupyter_base_cmd.""",
    ).tag(config=True)

    remove = Bool(
        False,
        config=True,
        help="""Delete containers when servers are stopped.""",
    )

    env_keep = List(
        [],
        help="""Override the env_keep of the Spawner calls, since we do not need
        to keep these env variables in the container.""",
    )

    def load_state(self, state):
        """Restore state about spawned single-user server after a hub restart.
        Local processes only need the process id.
        """
        super().load_state(state)
        if "cid" in state:
            self.cid = state["cid"]

    def get_state(self):
        """Save state that is needed to restore this spawner instance after a hub restore.
        Local processes only need the process id.
        """
        state = super().get_state()
        if self.cid:
            state["cid"] = self.cid
        return state

    def clear_state(self):
        """Clear stored state about this spawner (pid)"""
        super().clear_state()
        self.cid = None

    def user_env(self, env):
        """Augment environment of spawned process with user specific env variables."""
        if self.https_proxy:
            env["https_proxy"] = self.https_proxy
        return env

    def get_env(self):
        """Get the complete set of environment variables to be set in the spawned
        process.
        """
        env = super().get_env()
        env["JUPYTER_IMAGE_SPEC"] = self.image
        return env

    async def move_certs(self, paths):
        """Takes cert paths, moves and sets ownership for them
        Arguments:
            paths (dict): a list of paths for key, cert, and CA
        Returns:
            dict: a list (potentially altered) of paths for key, cert,
            and CA
        Stage certificates into a private home directory
        and make them readable by the user.
        """
        raise NotImplementedError

    async def start(self):
        """Start the single-user server."""
        # get_args() will set --port
        self.port = self.standard_jupyter_port

        podman_base_cmd = [
            "podman",
            "run",
            "-d",
            "--publish",
            f"{self.standard_jupyter_port}",
        ]
        if self.remove:
            podman_base_cmd.append("--rm")
        # append flags for the JUPYTER*** environment in the container
        jupyter_env = self.get_env()
        podman_base_cmd_jupyter_env = []
        for k, v in jupyter_env.items():
            podman_base_cmd_jupyter_env.append("--env")
            podman_base_cmd_jupyter_env.append("{k}={v}".format(k=k, v=v))
        podman_base_cmd += podman_base_cmd_jupyter_env

        jupyter_base_cmd = [self.image] + self.cmd + self.get_args()

        podman_cmd = podman_base_cmd + self.podman_additional_cmds
        jupyter_cmd = jupyter_base_cmd + self.jupyter_additional_cmds

        cmd = podman_cmd + jupyter_cmd

        env = self.user_env(os.environ.copy())

        self.log.info("Spawning via Podman command: " + " ".join(s for s in cmd))

        popen_kwargs = dict(
            stdout=PIPE,
            stderr=PIPE,
            start_new_session=True,  # don't forward signals
        )
        popen_kwargs.update(self.popen_kwargs)
        # don't let user config override env
        popen_kwargs["env"] = env

        # https://stackoverflow.com/questions/2502833/store-output-of-subprocess-popen-call-in-a-string

        if self.pull_image_first:
            pull_cmd = ["podman", "pull", self.pull_image]
            pull_proc = Popen(pull_cmd, **popen_kwargs)
            output, err = pull_proc.communicate()
            if pull_proc.returncode == 0:
                pass
            else:
                self.log.error(f"pull: {err}")
                raise RuntimeError(err)

        proc = Popen(cmd, **popen_kwargs)
        output, err = proc.communicate()
        if proc.returncode == 0:
            self.cid = output[:-2]
        else:
            self.log.error(f"run: {err}")
            raise RuntimeError(err)

        out, err, rc = self.podman("port", f"{self.standard_jupyter_port}")
        if rc != 0:
            self.log.error(f"port: {err}")
            raise RuntimeError(err)
        # out will have the form `0.0.0.0:12345`
        port = int(out.strip().split(b":")[-1])
        return ("127.0.0.1", port)

    async def poll(self):
        """Poll the spawned process to see if it is still running.
        If the process is still running, we return None. If it is not running,
        we return the exit code of the process if we have access to it, or 0 otherwise.
        """
        if not self.cid:
            return 0
        output, err, returncode = self.podman("inspect")
        if returncode == 0:
            state = json.loads(output)[0]["State"]
            if state["Running"]:
                return None
            else:
                return state["ExitCode"]
        else:
            self.log.error(f"inspect: {err}")
            raise RuntimeError(err)

    def podman(self, command, *args):
        cmd = ["podman", "container", command, self.cid] + list(args)
        popen_kwargs = dict(
            stdout=PIPE,
            stderr=PIPE,
            start_new_session=True,  # don't forward signals
            env=self.user_env(os.environ.copy()),
        )
        proc = Popen(cmd, **popen_kwargs)
        output, err = proc.communicate()
        return output, err, proc.returncode

    async def stop(self, now=False):
        """Stop the single-user server process for the current user.
        If `now` is False (default), shutdown the server as gracefully as possible,
        e.g. starting with SIGINT, then SIGTERM, then SIGKILL.
        If `now` is True, terminate the server immediately.
        The coroutine should return when the process is no longer running.
        """
        if not self.cid:
            return
        output, err, returncode = self.podman("stop")
        if returncode != 0:
            self.log.error(f"stop: {err}")
            raise RuntimeError(err)
