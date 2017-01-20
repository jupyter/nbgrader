import os
import re
import six

from textwrap import dedent
from traitlets import List, Unicode

from .base import BasePlugin


class CollectInfo(object):
    """Return object required by all
    :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` plugins.

    Keyword Arguments
    -----------------
    student_id: str
        The student id (This MUST be provided)
    file_id: str
        The file id (This MUST be provided)
    first_name: str
        The students first name (Optional)
    last_name: str
        The students last name (Optional)
    email: str
        The students email address (Optional)
    timestamp: str
        The submission timestamp (Optional, defaults to the current time)
    """

    def __init__(self, **kwargs):
        self.student_id = kwargs.get('student_id', None)
        self.file_id = kwargs.get('file_id', None)
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)
        self.email = kwargs.get('email', None)
        self.timestamp = kwargs.get('timestamp', None)

    def _validate(self, app):
        """Validate the provided class attributes."""
        attr_keys = [
            'student_id',
            'file_id',
            'first_name',
            'last_name',
            'email',
        ]

        for key in attr_keys:
            attr = getattr(self, key)
            if attr is None:
                if key in ['student_id', 'file_id']:
                    app.fail(
                        "Expected processor {} to provide the {} from the "
                        "submission file name."
                        "".format(app.collector_plugin.__name__, key)
                    )
            elif not isinstance(attr, six.string_types):
                app.fail(
                    "Expected processor {} to provide a string for {} from "
                    "the submission file name."
                    "".format(app.collector_plugin.__name__, key)
                )


class FileNameCollectorPlugin(BasePlugin):
    """Submission filename processor plugin for the
    :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp`.
    Subclasses MUST inherit from this class.
    """

    named_regexp = Unicode(
        default_value='',
        help=dedent(
            """
            This regular expression is applied to each submission filename and
            MUST be supplied by the instructor. This regular expression MUST
            provide the `(?P<student_id>...)` and `(?P<file_id>...)` named
            group expressions. Optionally this regular expression can also
            provide the `(?P<first_name>...)`, `(?P<last_name>...)`,
            `(?P<email>...)`, and `(?P<timestamp>...)` named group expressions.
            For example if the filename is:

                `ps1_bitdiddle_attempt_2016-01-30-15-00-00_problem1.ipynb`

            then this `named_regexp` could be:

                ".*_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"

            For named group regular expression examples see
            https://docs.python.org/howto/regex.html
            """
        )
    ).tag(config=True)

    valid_ext = List(
        default_value=['.ipynb'],
        help=dedent(
            """
            List of valid submission filename extensions to collect. Any
            submitted file with an extension not in this list is skipped.
            """
        )
    ).tag(config=True)

    def _match(self, filename):
        """Match the named group regular expression to the beginning of the
        filename and return the match groupdict or None if no match.
        """
        if not self.named_regexp:
            self.log.warn(
                "Regular expression not provided for plugin. Run with "
                "`--help-all` flag for more information."
            )
            return None

        match = re.match(self.named_regexp, filename)
        if not match or not match.groups():
            self.log.warn(
                "Regular expression '{}' did not match anything in filename."
                "".format(self.named_regexp)
            )
            return None

        gd = match.groupdict()
        self.log.debug(
            "Regular expression '{}' matched\n'{}' in filename."
            "".format(self.named_regexp, gd)
        )
        return gd

    def collect(self, submitted_file):
        """This is the main function called by the
        :class:`~nbgrader.apps.zipcollectapp.ZipCollectApp` for each submitted
        file. Note this function must also return a :class:`CollectApp`
        instance or None for sub-classed plugins.

        Parameters
        ----------
        submitted_file: str
            Each submitted file in the ``extracted_directory`` (absolute path).

        Returns
        -------
        :class:`CollectInfo` or None
            The collected data from the filename or None if the file should be
            skipped
        """
        root, ext = os.path.splitext(submitted_file)
        filename = os.path.basename(submitted_file)

        # Skip any files without the correct extension
        if ext not in self.valid_ext:
            self.log.debug("Invalid file extension {}".format(ext))
            return None

        kwargs = self._match(submitted_file)
        if not kwargs:
            return None
        return CollectInfo(**kwargs)
