"""Base formgrade authenticator."""
from traitlets.config.configurable import LoggingConfigurable


class BaseAuth(LoggingConfigurable):
    """Base formgrade authenticator."""

    def __init__(self, app, ip, port, base_directory, **kwargs):
        super(BaseAuth, self).__init__(**kwargs)
        self._app = app
        self._ip = ip
        self._port = port
        self._base_url = ''
        self._base_directory = base_directory

    @property
    def base_url(self):
        return self._base_url

    def authenticate(self):
        """Authenticate a request.
        Returns a boolean or flask redirect."""
        return True

    def notebook_server_exists(self):
        """Checks for a notebook server."""
        return False

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        raise NotImplemented

    def stop(self, sig):
        """Stops the notebook server."""
        pass
