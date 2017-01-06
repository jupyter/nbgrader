"""JupyterHub authenticator."""
import requests
import os
import json
import sys
import urllib

from subprocess import check_output
from traitlets import Unicode, Int, List, Bool, Instance, observe, default
from six.moves.urllib.parse import unquote
from tornado import web
from textwrap import dedent

try:
    from jupyterhub.services.auth import HubAuth as JupyterHubAuth
    JupyterHubAuth.__name__ = "JupyterHubAuth"
except ImportError:
    JupyterHubAuth = None

from .base import BaseAuth


class HubAuth(BaseAuth):
    """Jupyter hub authenticator."""

    graders = List([], help="List of JupyterHub user names allowed to grade.").tag(config=True)

    if JupyterHubAuth:
        hub_authenticator = Instance(JupyterHubAuth)
    else:
        hub_authenticator = None

    @default("hub_authenticator")
    def _hub_authenticator_default(self):
        auth = JupyterHubAuth(parent=self)
        auth.login_url = '/hub/login'
        auth.api_url = self.hubapi_base_url
        auth.api_token = self.hubapi_token
        return auth

    hub_base_url = Unicode(
        os.environ.get('JUPYTERHUB_BASE_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. Provided by JupyterHub in the
            JUPYTERHUB_BASE_URL environment variable.
            """
        )
    ).tag(config=True)

    hubapi_base_url = Unicode(
        os.environ.get('JUPYTERHUB_API_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. Provided by JupyterHub in the
            JUPYTERHUB_API_URL environment variable.
            """
        )
    ).tag(config=True)

    hubapi_token = Unicode(
        os.environ.get('JUPYTERHUB_API_TOKEN', ''),
        help=dedent(
            """
            JupyterHub API auth token. Provided by JupyterHub in the
            JUPYTERHUB_API_TOKEN environment variable.
            """
        )
    ).tag(config=True)

    notebook_url_prefix = Unicode(None, allow_none=True, help="""
        Relative path of the formgrader with respect to the hub's user base
        directory.  No trailing slash. i.e. "Documents" or "Documents/notebooks". """).tag(config=True)

    @observe("notebook_url_prefix")
    def _notebook_url_prefix_changed(self, change):
        self.notebook_url_prefix = change['new'].strip('/')

    remap_url = Unicode(
        os.environ.get('JUPYTERHUB_SERVICE_PREFIX', ''),
        help=dedent(
            """
            Suffix appended to `HubAuth.hub_base_url` to form the full URL to
            the formgrade server. Provided by JupyterHub in the
            JUPYTERHUB_SERVICE_PREFIX environment variable.
            """
        )
    ).tag(config=True)

    notebook_server_user = Unicode(
        '',
        help=dedent(
            """
            The user that hosts the autograded notebooks. By default, this is
            just the user that is logged in, but if that user is an admin user
            and has the ability to access other users' servers, then this
            variable can be set, allowing them to access the notebook server
            with the autograded notebooks.
            """
        )
    ).tag(config=True)

    @observe("config")
    def _config_changed(self, change):
        new = change['new']

        if 'proxy_address' in new.HubAuth:
            raise ValueError(
                "HubAuth.proxy_address is no longer a valid configuration "
                "option."
            )

        if 'proxy_port' in new.HubAuth:
            raise ValueError(
                "HubAuth.proxy_port is no longer a valid configuration "
                "option."
            )

        if 'proxy_base_url' in new.HubAuth:
            raise ValueError(
                "HubAuth.proxy_base_url is no longer a valid configuration "
                "option."
            )

        if 'hub_address' in new.HubAuth:
            raise ValueError(
                "HubAuth.hub_address is no longer a valid configuration "
                "option, please use HubAuth.hub_base_url instead."
            )

        if 'hub_port' in new.HubAuth:
            raise ValueError(
                "HubAuth.hub_port is no longer a valid configuration "
                "option, please use HubAuth.hub_base_url instead."
            )

        if 'hubapi_address' in new.HubAuth:
            raise ValueError(
                "HubAuth.hubapi_address is no longer a valid configuration "
                "option, please use HubAuth.hubapi_base_url instead."
            )

        if 'hubapi_port' in new.HubAuth:
            raise ValueError(
                "HubAuth.hubapi_port is no longer a valid configuration "
                "option, please use HubAuth.hubapi_base_url instead."
            )

        super(HubAuth, self)._config_changed(change)

    def __init__(self, *args, **kwargs):
        super(HubAuth, self).__init__(*args, **kwargs)
        self._user = None
        self._base_url = urllib.parse.urljoin(self.hub_base_url, self.remap_url.lstrip("/"))

        self.log.debug("hub_base_url: %s", self.hub_base_url)
        self.log.debug("hubapi_base_url: %s", self.hubapi_base_url)
        self.log.debug("hubapi_token: %s", self.hubapi_token)
        self.log.debug("remap_url: %s", self.remap_url)
        self.log.debug("base_url: %s", self.base_url)

        # sanity check that we are running where JupyterHub thinks we are running
        true_url = "http://{}:{}".format(self._ip, self._port)
        jhub_url = os.environ.get("JUPYTERHUB_SERVICE_URL", "")
        if true_url != jhub_url:
            self.log.warn(
                "The formgrader is running at %s, but JupyterHub thinks it is running at %s ...",
                true_url, jhub_url)

    @property
    def login_url(self):
        return self.hub_authenticator.login_url

    def add_remap_url_prefix(self, url):
        if url == '/':
            return self.remap_url + '/?'
        else:
            return self.remap_url + url

    def transform_handler(self, handler):
        new_handler = list(handler)

        # transform the handler url
        url = self.add_remap_url_prefix(handler[0])
        new_handler[0] = url

        # transform any urls in the arguments
        if len(handler) > 2:
            new_args = handler[2].copy()
            if 'url' in new_args:
                new_args['url'] = self.add_remap_url_prefix(new_args['url'])
            new_handler[2] = new_args

        return tuple(new_handler)

    def get_user(self, handler):
        user_model = self.hub_authenticator.get_user(handler)
        if user_model:
            return user_model['name']
        return None

    def authenticate(self, user):
        """Authenticate a request.
        Returns a boolean or redirect."""

        # Check if the user name is registered as a grader.
        if user in self.graders:
            self._user = user
            return True

        self.log.warn('Unauthorized user "%s" attempted to access the formgrader.' % user)
        return False

    def notebook_server_exists(self):
        """Does the notebook server exist?"""
        if self.notebook_server_user:
            user = self.notebook_server_user
        else:
            user = self._user

        # first check if the server is running
        response = self._hubapi_request('/users/{}'.format(user))
        if response.status_code == 200:
            user_data = response.json()
        else:
            self.log.warn("Could not access information about user {} (response: {} {})".format(
                user, response.status_code, response.reason))
            return False

        # start it if it's not running
        if user_data['server'] is None and user_data['pending'] != 'spawn':
            # start the server
            response = self._hubapi_request('/users/{}/server'.format(user), method='POST')
            if response.status_code not in (201, 202):
                self.log.warn("Could not start server for user {} (response: {} {})".format(
                    user, response.status_code, response.reason))
                return False

        return True

    def get_notebook_server_cookie(self):
        # same user, so no need to request admin access
        if not self.notebook_server_user:
            return None

        # request admin access to the user's server
        response = self._hubapi_request('/users/{}/admin-access'.format(self.notebook_server_user), method='POST')
        if response.status_code != 200:
            self.log.warn("Failed to gain admin access to user {}'s server (response: {} {})".format(
                self.notebook_server_user, response.status_code, response.reason))
            return None

        # access granted!
        cookie_name = 'jupyter-hub-token-{}'.format(self.notebook_server_user)
        notebook_server_cookie = unquote(response.cookies[cookie_name][1:-1])
        cookie = {
            'name': cookie_name,
            'value': notebook_server_cookie,
            'path': '/user/{}'.format(self.notebook_server_user)
        }

        return cookie

    def get_notebook_url(self, relative_path):
        """Gets the notebook's url."""
        if self.notebook_url_prefix is not None:
            relative_path = self.notebook_url_prefix + '/' + relative_path
        if self.notebook_server_user:
            user = self.notebook_server_user
        else:
            user = self._user
        return "{}/user/{}/notebooks/{}".format(self.hub_base_url, user, relative_path)

    def _hubapi_request(self, relative_path, method='GET', body=None):
        data = body
        if isinstance(data, (dict,)):
            data = json.dumps(data)

        return requests.request(method, self.hubapi_base_url + relative_path, headers={
            'Authorization': 'token %s' % self.hubapi_token
        }, data=data)
