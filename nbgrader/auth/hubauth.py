"""JupyterHub authenticator."""
import requests
import os

from traitlets import Unicode, List, Instance, observe, default
from six.moves.urllib.parse import unquote, urljoin
from textwrap import dedent

try:
    from jupyterhub.services.auth import HubAuth as JupyterHubAuth
    JupyterHubAuth.__name__ = "JupyterHubAuth"
except ImportError:
    JupyterHubAuth = None

from .base import BaseAuth


class HubAuth(BaseAuth):
    """Jupyter hub authenticator."""

    ############################################################################
    # These are options you typically want to change:

    graders = List(
        [], help="List of JupyterHub user names allowed to grade."
    ).tag(config=True)

    notebook_url_prefix = Unicode(
        None, allow_none=True,
        help=dedent(
            """
            Relative path of nbgrader directory with respect to
            notebook_server_user's base directory. No trailing slash, i.e.
            "assignments" or "assignments/course101". This is used for accessing
            the *live* version of notebooks via JupyterHub. If you don't want to
            access the live notebooks and are fine with just the static
            interface provided by the formgrader, then you can ignore this
            option.
            """
        )
    ).tag(config=True)
    @observe("notebook_url_prefix")
    def _notebook_url_prefix_changed(self, change):
        self.notebook_url_prefix = change['new'].strip('/')

    notebook_server_user = Unicode(
        '',
        help=dedent(
            """
            The user that hosts the autograded notebooks. This is the only user
            that is able to actually access the *live* version of the
            autograded notebooks.
            """
        )
    ).tag(config=True)

    ############################################################################
    # These are options you typically do NOT want to change:

    if JupyterHubAuth:
        hub_authenticator = Instance(JupyterHubAuth)
    else:
        hub_authenticator = None

    @default("hub_authenticator")
    def _hub_authenticator_default(self):
        auth = JupyterHubAuth(parent=self)
        auth.api_url = self.hubapi_base_url
        auth.api_token = self.hubapi_token
        return auth

    hub_base_url = Unicode(
        os.environ.get('JUPYTERHUB_BASE_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. When run as a managed service, this
            value is provided by JupyterHub in the JUPYTERHUB_BASE_URL
            environment variable.
            """
        )
    ).tag(config=True)

    hubapi_base_url = Unicode(
        os.environ.get('JUPYTERHUB_API_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. When run as a managed service, this
            value is provided by JupyterHub in the JUPYTERHUB_API_URL
            environment variable.
            """
        )
    ).tag(config=True)

    hubapi_token = Unicode(
        os.environ.get('JUPYTERHUB_API_TOKEN', ''),
        help=dedent(
            """
            JupyterHub API auth token. When run as a managed service, this value
            is provided by JupyterHub in the JUPYTERHUB_API_TOKEN environment
            variable.
            """
        )
    ).tag(config=True)

    remap_url = Unicode(
        os.environ.get('JUPYTERHUB_SERVICE_PREFIX', ''),
        help=dedent(
            """
            Suffix appended to `HubAuth.hub_base_url` to form the full URL to
            the formgrade server. When run as a managed service, this value is
            provided by JupyterHub in the JUPYTERHUB_SERVICE_PREFIX environment
            variable.
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

    ############################################################################
    # Begin formgrader implementation

    def __init__(self, *args, **kwargs):
        super(HubAuth, self).__init__(*args, **kwargs)
        self._user = None
        self._base_url = urljoin(self.hub_base_url, self.remap_url.lstrip("/"))

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
        """Used by tornado to redirect users to the correct login page when
        they are not authenticated."""
        return self.hub_authenticator.login_url

    def add_remap_url_prefix(self, url):
        """This function is used to remap urls to use the correct JupyterHub prefix.

        For example, if someone requests /assignments/ps1, and the formgrader is
        running at /services/formgrader, then this function will map:

        /assignments/ps1 --> /services/formgrader/assignments/ps1

        Arguments
        ---------
        url: str
            The requested URL

        Returns
        -------
        remapped_url: str
            The remapped URL, with the relevant prefix added

        """
        if url == '/':
            return self.remap_url + '/?'
        else:
            return self.remap_url + url

    def transform_handler(self, handler):
        """Transform a tornado handler to use the correct JupyterHub prefix.

        By default, all the formgrader handlers are listening at /, e.g.
        /assignments/ps1. But when running with JupyterHub, we need to prefix
        the handlers' URLs to use the correct prefix, so they listen (for
        example) at /services/formgrader/assignments/ps1.

        Arguments
        ---------
        handler: tuple
            A tuple defining the Tornado handler, where the first element is
            the route, the second element is the handler class, and the third
            element (if present) is arguments for the handler.

        Returns
        -------
        handler: tuple
            A new handler tuple, with the same semantics as the inputs.

        """
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
        """Get the Hub user for a given tornado handler.

        Checks cookie with the Hub to identify the current user.

        Arguments
        ---------
        handler: tornado.web.RequestHandler
            The current request handler

        Returns
        -------
        user: str
            The user's name, or None if authentication failed.

        """
        user_model = self.hub_authenticator.get_user(handler)
        if user_model:
            return user_model['name']
        return None

    def authenticate(self, user):
        """Determine whether the user has permission to access the formgrader.

        Arguments
        ---------
        user: str
            The user trying to access the formgrader (returned by get_user)

        Returns
        -------
        authenticated: bool
            Whether the user is allowed to access the formgrader.

        """
        # Check if the user name is registered as a grader.
        if user in self.graders:
            self._user = user
            return True

        self.log.warn('Unauthorized user "%s" attempted to access the formgrader.' % user)
        return False

    def notebook_server_exists(self):
        """Determine whether a live notebook server exists.

        The live notebook can only be accessed by notebook_server_user. Any
        other user (even if they have access to the formgrader) will,
        unfortunately, not be able to access the live notebooks.

        Returns
        -------
        exists: bool
            Whether the server can be accessed and is running

        """
        return self.notebook_server_user == self._user

    def get_notebook_url(self, relative_path):
        """Get the full URL to a notebook, given its relative path.

        This assumes that notebooks live at:

        <hub_base_url>/user/<username>/notebooks/<notebook_url_prefix>/<relative_path>

        where <hub_base_url> is a config option, <username> is either the
        notebook_server_user (if set) or the current user, <notebook_url_prefix>
        is the nbgrader directory (a config option), and <relative_path> is the
        given argument.

        Arguments
        ---------
        relative_path: str
            Path to a notebook, relative to the nbgrader directory.

        Returns
        -------
        path: str
            Full URL to the notebook

        """
        if self.notebook_url_prefix is not None:
            relative_path = self.notebook_url_prefix + '/' + relative_path

        return urljoin(
            self.hub_base_url,
            urljoin("user/{}/notebooks/".format(self.notebook_server_user), relative_path))
