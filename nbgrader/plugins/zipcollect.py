import os
import re
import six

from textwrap import dedent
from traitlets import List, Unicode

from .base import BasePlugin


class CollectInfo(object):

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
                        "Expected processor {} to provide the {}."
                        "".format(app.plugin_class.__name__, key)
                    )
            elif not isinstance(attr, six.string_types):
                app.fail(
                    "Expected processor {} to provide a string for {}."
                    "".format(app.plugin_class.__name__, key)
                )


class FileNameProcessor(BasePlugin):

    student_id_regexp = Unicode(
        '', help="TODO"
    ).tag(config=True)

    notebook_id_regexp = Unicode(
        '', help="TODO"
    ).tag(config=True)

    first_name_regexp = Unicode(
        '', help="TODO"
    ).tag(config=True)

    last_name_regexp = Unicode(
        '', help="TODO"
    ).tag(config=True)

    timestamp_regexp = Unicode(
        '', help="TODO"
    ).tag(config=True)

    valid_ext = List(
        ['.ipynb'],
        help="TODO"
    ).tag(config=True)

    def match(self, exp, string):
        if not exp or exp is None:
            return None

        match = re.search(exp, string)
        if not match:
            return None
        return match.group(0)

    def collect(self, submitted_file):
        root, ext = os.path.splitext(submitted_file)
        filename = os.path.basename(root)

        # Skip any files without the correct extension
        if ext.lower() not in self.valid_ext:
            return None

        info = CollectInfo(
            student_id=self.match(self.student_id_regexp, filename),
            notebook_id=self.match(self.notebook_id_regexp, filename),
            first_name=self.match(self.first_name_regexp, filename),
            last_name=self.match(self.last_name_regexp, filename),
            timestamp=self.match(self.timestamp_regexp, filename),
        )

        return info
