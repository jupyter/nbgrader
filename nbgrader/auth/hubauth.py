"""JupyterHub authenticator."""
import requests
import os
from flask import request, redirect, abort
from IPython.utils.traitlets import Unicode, Int
from .base import BaseAuth


class HubAuth(BaseAuth):
    """Jupyter hub authenticator."""

    hub_address = Unicode(None, config=True, help="""Address of the
        running Jupyter hub server.""", allow_none=True)
    hub_port = Int(8000, config=True, help="Port of the running Jupyter hub server.")
    hub_cookie = Unicode("jupyter-hub-token-jon", config=True, help="""Name of the cookie
        used by JupyterHub""")

    def __init__(self, *args, **kwargs):
        super(HubAuth, self).__init__(*args, **kwargs)

        # Save auth token.
        self._token = os.environ.get('JPY_API_TOKEN')

        # If the hub address isn't set, assume that it's on the same machine
        # as the formgrader server.
        if self.hub_address is None:
            self.hub_address = self._ip

        # Make the hub base URL
        self._hub_base = 'http://{}:{}'.format(self.hub_address, self.hub_port)

    def authenticate(self):
        """Authenticate a request.
        Returns a boolean or flask redirect."""
        # TODO: Implement me!

        # If auth cookie doesn't exist, redirect to the login page with
        # next set to redirect back to the this page.

        # Check with the Hub to see if the auth cookie is valid.

        # If it's not valid, return false.
        return True

    def notebook_server_exists(self):
        """Does the notebook server exist?"""
        return True

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        # TODO
        return "http://{}:{}/notebooks/{}".format(
            self.hub_address,
            self.hub_port,
            relative_path)

    def _tokened_request(self, relative_path):
        return requests.request('GET', self._hub_base + relative_path,  headers={
            'Authorization': 'token %s' % self._token
        })
