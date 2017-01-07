"""No authentication authenticator."""
from textwrap import dedent
from traitlets import Unicode, observe
from six.moves.urllib.parse import urljoin

from .base import BaseAuth


class NotebookAuth(BaseAuth):
    """Notebook server authenticator."""

    notebook_base_url = Unicode(
        '/',
        help="Base URL of the notebook server."
    ).tag(config=True)

    notebook_url_prefix = Unicode(
        None, allow_none=True,
        help=dedent(
            """
            Relative path of the formgrader with respect to the notebook's base
            directory.  No trailing slash. i.e. "Documents" or
            "Documents/notebooks".
            """
        )
    ).tag(config=True)
    @observe("notebook_url_prefix")
    def _notebook_url_prefix_changed(self, change):
        self.notebook_url_prefix = change['new'].strip('/')

    remap_url = Unicode(
        '/formgrader',
        help=dedent(
            """
            Suffix appened to `NotebookAuth.notebook_base_url` to form the full
            URL to the formgrade server.  By default this is '/formgrader'.
            """
        )
    ).tag(config=True)
    @observe("remap_url")
    def _remap_url_changed(self, change):
        self.remap_url = change['new'].rstrip('/')

    def __init__(self, *args, **kwargs):
        super(NotebookAuth, self).__init__(*args, **kwargs)
        self._base_url = urljoin(self.notebook_base_url, self.remap_url.lstrip("/"))

    @property
    def full_url(self):
        return urljoin("http://{}:{}".format(self._ip, self._port), self._base_url)

    def add_remap_url_prefix(self, url):
        """This function is used to remap urls to use the correct notebook prefix.

        For example, if someone requests /assignments/ps1, and the formgrader is
        running at /formgrader, then this function will map:

        /assignments/ps1 --> /formgrader/assignments/ps1

        Arguments
        ---------
        url: str
            The requested URL

        Returns
        -------
        remapped_url: str
            The remapped URL, with the relevant prefix added

        """
        prefix = urljoin(self.notebook_base_url, self.remap_url.lstrip('/'))
        if url == '/':
            return prefix + '/?'
        else:
            if not url.startswith('/'):
                return prefix + '/' + url
            else:
                return prefix + url

    def transform_handler(self, handler):
        """Transform a tornado handler to use the correct notebook prefix.

        By default, all the formgrader handlers are listening at /, e.g.
        /assignments/ps1. But when running with the notebook, we need to prefix
        the handlers' URLs to use the correct prefix, so they listen (for
        example) at /formgrader/assignments/ps1.

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

    def notebook_server_exists(self):
        """We are running as part of the notebook, so the notebook server will
        always exist!"""
        return True

    def get_notebook_url(self, relative_path):
        """Get the full URL to a notebook, given its relative path.

        This assumes that notebooks live at:

        <notebook_base_url>/notebooks/<notebook_url_prefix>/<relative_path>

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
            self.notebook_base_url,
            "notebooks/{}".format(relative_path))
