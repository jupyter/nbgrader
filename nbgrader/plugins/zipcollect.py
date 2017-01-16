import os
import re
import six

from textwrap import dedent
from traitlets import List, Unicode

from .base import BasePlugin


class CollectInfo(object):
    """TODO"""

    def __init__(self, **kwargs):
        self.student_id = kwargs.get('student_id', None)
        self.notebook_id = kwargs.get('notebook_id', None)
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)
        self.email = kwargs.get('email', None)
        self.timestamp = kwargs.get('timestamp', None)

    # XXX Is there a better way to do this with traitlets?
    def _validate(self, app):
        attr_keys = [
            'student_id',
            'notebook_id',
            'first_name',
            'last_name',
            'email',
        ]

        for key in attr_keys:
            attr = getattr(self, key)
            if attr is None:
                if key in ['student_id', 'notebook_id']:
                    app.fail(
                        "Expected processor {} to provide the {} from the "
                        "submission file name."
                        "".format(app.plugin_class.__name__, key)
                    )
            elif not isinstance(attr, six.string_types):
                app.fail(
                    "Expected processor {} to provide a string for {} from "
                    "the submission file name."
                    "".format(app.plugin_class.__name__, key)
                )


class FileNameProcessor(BasePlugin):
    """Submission filename processor plugin for the ZipCollectApp"""

    student_id_regexp = Unicode(
        '',
        help=dedent(
            """
            Regular expression for matching the student_id in the submission
            file filename."
            """
        )
    ).tag(config=True)

    notebook_id_regexp = Unicode(
        '',
        help=dedent(
            """
            Regular expression for matching the notebook_id in the submission
            file filename."
            """
        )
    ).tag(config=True)

    first_name_regexp = Unicode(
        '',
        help=dedent(
            """
            Regular expression for matching the students first name in the
            submission file filename."
            """
        )
    ).tag(config=True)

    last_name_regexp = Unicode(
        '',
        help=dedent(
            """
            Regular expression for matching the students last name in the
            submission file filename."
            """
        )
    ).tag(config=True)

    timestamp_regexp = Unicode(
        '',
        help=dedent(
            """
            Regular expression for matching the submission timestamp in the
            submission file filename."
            """
        )
    ).tag(config=True)

    valid_ext = List(
        ['.ipynb'],
        help=dedent(
            """
            List of valid submission filename extensions to collect. Any
            submitted file with an extension not in this list is skipped.
            """
        )
    ).tag(config=True)

    def match(self, exp, string, key):
        if not exp or exp is None:
            self.log.debug(
                "No regular expression given to match {} in filename."
                "".format(key)
            )
            return None

        match = re.search(re.compile(exp), string)
        if not match or not match.groups():
            self.log.debug(
                "{} regular expression '{}' did not match anything in filename."
                "".format(key, exp)
            )
            return None

        self.log.debug(
            "{} regular expression '{}' matched '{}' in filename."
            "".format(key, exp, match.group(1))
        )
        return match.group(1)

    def collect(self, submitted_file):
        root, ext = os.path.splitext(submitted_file)
        filename = os.path.basename(submitted_file)

        # Skip any files without the correct extension
        if ext not in self.valid_ext:
            return None

        info = CollectInfo(
            student_id=self.match(self.student_id_regexp, filename, 'student_id'),
            notebook_id=self.match(self.notebook_id_regexp, filename, 'notebook_id'),
            first_name=self.match(self.first_name_regexp, filename, 'first_name'),
            last_name=self.match(self.last_name_regexp, filename, 'last_name'),
            timestamp=self.match(self.timestamp_regexp, filename, 'timestamp'),
        )

        return info
