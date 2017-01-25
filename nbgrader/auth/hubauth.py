"""JupyterHub authenticator."""
import os
import sys

from traitlets import Unicode, Instance, observe, default
from six.moves.urllib.parse import urljoin
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

    grader_group = Unicode(
        '',
        help=dedent(
            """
            Name of the JupyterHub group containing users who are allowed to
            access the formgrader. This MUST be specified in your config file.
            """
        ),
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
        auth.api_url = self.jupyterhub_api_url
        auth.api_token = self.jupyterhub_api_token
        return auth

    jupyterhub_base_url = Unicode(
        os.environ.get('JUPYTERHUB_BASE_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. When run as a managed service, this
            value is provided by JupyterHub in the JUPYTERHUB_BASE_URL
            environment variable.
            """
        )
    ).tag(config=True)

    jupyterhub_api_url = Unicode(
        os.environ.get('JUPYTERHUB_API_URL', ''),
        help=dedent(
            """
            Base URL of the hub server. When run as a managed service, this
            value is provided by JupyterHub in the JUPYTERHUB_API_URL
            environment variable.
            """
        )
    ).tag(config=True)

    jupyterhub_api_token = Unicode(
        os.environ.get('JUPYTERHUB_API_TOKEN', ''),
        help=dedent(
            """
            JupyterHub API auth token. When run as a managed service, this value
            is provided by JupyterHub in the JUPYTERHUB_API_TOKEN environment
            variable.
            """
        )
    ).tag(config=True)

    jupyterhub_service_prefix = Unicode(
        os.environ.get('JUPYTERHUB_SERVICE_PREFIX', ''),
        help=dedent(
            """
            Suffix appended to `HubAuth.jupyterhub_base_url` to form the full URL to
            the formgrade server. When run as a managed service, this value is
            provided by JupyterHub in the JUPYTERHUB_SERVICE_PREFIX environment
            variable.
            """
        )
    ).tag(config=True)

    def _load_config(self, cfg, **kwargs):
        def check_option(name, instead=None):
            if name in cfg.HubAuth:
                msg = "HubAuth.{} is no longer a valid configuration option.".format(name)
                if instead:
                    msg += " Please use HubAuth.{} instead.".format(instead)
                    msg += (
                        " However, note that you probably do not even need to "
                        "configure this option anymore!")

                raise ValueError(msg)

        check_option("proxy_address")
        check_option("proxy_base_url")
        check_option("proxy_port")

        check_option("graders", "grader_group")
        check_option("hub_address", "jupyterhub_base_url")
        check_option("hub_base_url", "jupyterhub_base_url")
        check_option("hub_port", "jupyterhub_base_url")
        check_option("hubapi_address", "jupyterhub_api_url")
        check_option("hubapi_base_url", "jupyterhub_api_url")
        check_option("hubapi_port", "jupyterhub_api_url")
        check_option("hubapi_token", "jupyterhub_api_token")
        check_option("remap_url", "jupyterhub_service_prefix")

        super(HubAuth, self)._load_config(cfg, **kwargs)

    ############################################################################
    # Begin formgrader implementation

    def __init__(self, *args, **kwargs):
        super(HubAuth, self).__init__(*args, **kwargs)

        if self.grader_group == '':
            self.log_error("The config option grader_group must be specified")
            sys.exit(1)

        self._user = None
        self._base_url = self.jupyterhub_service_prefix

        self.log.debug("jupyterhub_base_url: %s", self.jupyterhub_base_url)
        self.log.debug("jupyterhub_api_url: %s", self.jupyterhub_api_url)
        self.log.debug("jupyterhub_api_token: %s", self.jupyterhub_api_token)
        self.log.debug("jupyterhub_service_prefix: %s", self.jupyterhub_service_prefix)
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

    def add_jupyterhub_service_prefix(self, url):
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
            return self.jupyterhub_service_prefix + '/?'
        else:
            return self.jupyterhub_service_prefix + url

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
        url = self.add_jupyterhub_service_prefix(handler[0])
        new_handler[0] = url

        # transform any urls in the arguments
        if len(handler) > 2:
            new_args = handler[2].copy()
            if 'url' in new_args:
                new_args['url'] = self.add_jupyterhub_service_prefix(new_args['url'])
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
        user: dict
            The user model, or None if authentication failed.

        """
        return self.hub_authenticator.get_user(handler)

    def authenticate(self, user_model):
        """Determine whether the user has permission to access the formgrader.

        Arguments
        ---------
        user_model: dict
            The user trying to access the formgrader (returned by get_user)

        Returns
        -------
        authenticated: bool
            Whether the user is allowed to access the formgrader.

        """
        # Check if the user name is registered as a grader.
        if self.grader_group in user_model['groups']:
            self._user = user_model['name']
            return True

        self.log.warn('Unauthorized user "%s" attempted to access the formgrader.' % user_model['name'])
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

        <jupyterhub_base_url>/user/<username>/notebooks/<notebook_url_prefix>/<relative_path>

        where <jupyterhub_base_url> is a config option, <username> is either the
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
            self.jupyterhub_base_url,
            "user/{}/notebooks/{}".format(self.notebook_server_user, relative_path))
