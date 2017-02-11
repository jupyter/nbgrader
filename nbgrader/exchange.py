import os
import datetime

from textwrap import dedent

from dateutil.tz import gettz
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, Bool, default
from jupyter_core.paths import jupyter_data_dir

from .utils import check_directory


class Exchange(LoggingConfigurable):

    course_id = Unicode(
        '',
        help=dedent(
            """
            A key that is unique per instructor and course. This MUST be
            specified, either by setting the config option, or using the
            --course option on the command line.
            """
        )
    ).tag(config=True)

    timezone = Unicode(
        "UTC",
        help="Timezone for recording timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z",
        help="Format string for timestamps"
    ).tag(config=True)

    root = Unicode(
        "/srv/nbgrader/exchange",
        help="The nbgrader exchange directory writable to everyone. MUST be preexisting."
    ).tag(config=True)

    cache = Unicode(
        "",
        help="Local cache directory for nbgrader submit and nbgrader list. Defaults to $JUPYTER_DATA_DIR/nbgrader_cache"
    ).tag(config=True)

    @default("cache")
    def _cache_default(self):
        return os.path.join(jupyter_data_dir(), 'nbgrader_cache')

    path_includes_course = Bool(
        False,
        help=dedent(
            """
            Whether the path for fetching/submitting  assignments should be
            prefixed with the course name. If this is `False`, then the path
            will be something like `./ps1`. If this is `True`, then the path
            will be something like `./course123/ps1`.
            """
        )
    ).tag(config=True)

    def set_timestamp(self):
        """Set the timestap using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)

    def set_perms(self, dest, perms):
        all_dirs = []
        for dirname, _, filenames in os.walk(dest):
            for filename in filenames:
                os.chmod(os.path.join(dirname, filename), perms)
            all_dirs.append(dirname)

        for dirname in all_dirs[::-1]:
            os.chmod(dirname, perms)

    def ensure_root(self):
        """See if the exchange directory exists and is writable, fail if not."""
        if not check_directory(self.root, write=True, execute=True):
            self.fail("Unwritable directory, please contact your instructor: {}".format(self.root))
