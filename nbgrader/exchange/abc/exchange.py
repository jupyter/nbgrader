import os
import datetime
import sys

from textwrap import dedent

from dateutil.tz import gettz
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, Bool, Instance, Type, default, validate
from jupyter_core.paths import jupyter_data_dir

from nbgrader.utils import check_directory, ignore_patterns, self_owned
from nbgrader.coursedir import CourseDirectory
from nbgrader.auth import Authenticator


class ExchangeError(Exception):
    pass


class Exchange(LoggingConfigurable):
    timezone = Unicode(
        "UTC",
        help="Timezone for recording timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S.%f %Z",
        help="Format string for timestamps"
    ).tag(config=True)

    coursedir = Instance(CourseDirectory, allow_none=True)
    authenticator = Instance(Authenticator, allow_none=True)

    def __init__(self, coursedir=None, authenticator=None, **kwargs):
        self.coursedir = coursedir
        self.authenticator = authenticator
        super(Exchange, self).__init__(**kwargs)

    def fail(self, msg):
        self.log.fatal(msg)
        raise ExchangeError(msg)

    def set_timestamp(self):
        """Set the timestap using the configured timezone."""
        tz = gettz(self.timezone)
        if tz is None:
            self.fail("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)

    def init_src(self):
        """Compute and check the source paths for the transfer."""
        raise NotImplementedError

    def init_dest(self):
        """Compute and check the destination paths for the transfer."""
        raise NotImplementedError

    def copy_files(self):
        """Actually do the file transfer."""
        raise NotImplementedError

    def start(self):
        self.set_timestamp()

        self.init_src()
        self.init_dest()
        self.copy_files()
