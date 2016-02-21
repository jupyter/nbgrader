"""No authentication authenticator."""
import socket
import os
import subprocess as sp
import time
import sys
import signal

from textwrap import dedent
from traitlets import Bool, Integer, Unicode

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
    nbserver_port = Integer(config=True, help="Port for the notebook server")

    def _nbserver_port_default(self):
        return random_port()

    def __init__(self, *args, **kwargs):
        super(NoAuth, self).__init__(*args, **kwargs)

        # first launch a notebook server
        if self.start_nbserver:
            notebookapp = os.path.normpath(os.path.join(
                os.path.dirname(__file__), "..", "apps", "notebookapp.py"))

            if self._ip == "0.0.0.0":
                self.log.warning(
                    "I will launch the notebook server on '0.0.0.0'. Note that this may prevent "
                    "access to the notebooks because 0.0.0.0 is usually not an accessible "
                    "IP address. You probably want to set the formgrader IP to something that "
                    "is accessible from the outside world.")

            kwargs = dict(
                cwd=self._base_directory,
                env=os.environ.copy()
            )
            if sys.platform == 'win32':
                kwargs['creationflags'] = sp.CREATE_NEW_PROCESS_GROUP

            self._notebook_server_ip = self._ip
            self._notebook_server_port = str(self.nbserver_port)
            self._notebook_server = sp.Popen(
                [
                    sys.executable, notebookapp,
                    "--ip", self._notebook_server_ip,
                    "--port", self._notebook_server_port
                ],
                **kwargs)
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

    def stop(self):
        """Stops the notebook server."""
        if self.notebook_server_exists():
            self.log.info("Stopping notebook server...")
            if sys.platform == 'win32':
                self._notebook_server.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self._notebook_server.terminate()

            for i in range(10):
                retcode = self._notebook_server.poll()
                if retcode is not None:
                    self._notebook_server_exists = False
                    break
                time.sleep(0.1)

            if retcode is None:
                self.log.critical("Couldn't shutdown notebook server, force killing it")
                self._notebook_server.kill()

            self._notebook_server.wait()
