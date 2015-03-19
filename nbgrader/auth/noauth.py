"""No authentication authenticator."""
import socket
import os
import subprocess as sp
from IPython.utils.traitlets import Bool

from .base import BaseAuth


def random_port():
    """Get a single random port"""
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class NoAuth(BaseAuth):
    """Pass through authenticator."""

    start_nbserver = Bool(True, config=True, help=""""Start a single notebook
        server that allows submissions to be viewed.""")

    def __init__(self, *args, **kwargs):
        super(NoAuth, self).__init__(*args, **kwargs)

        # first launch a notebook server
        if self.start_nbserver:
            self._notebook_server_ip = self._ip
            self._notebook_server_port = str(random_port())
            self._notebook_server = sp.Popen(
                [
                    "python", os.path.join(os.path.dirname(__file__), "..", "apps", "notebookapp.py"),
                    "--ip", self._notebook_server_ip,
                    "--port", self._notebook_server_port
                ],
                cwd=self._base_directory)
            self._notebook_server_exists = True
        else:
            self._notebook_server_exists = False

    def notebook_server_exists(self):
        """Does the notebook server exist?"""
        return self._notebook_server_exists

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        return "http://{}:{}/notebooks/{}".format(
            self._notebook_server_ip,
            self._notebook_server_port,
            relative_path)
