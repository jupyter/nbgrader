#!/usr/bin/env python

import os.path
import sys
import nbgrader.apps

try:
    from StringIO import StringIO # Python 2
except ImportError:
    from io import StringIO # Python 3

header = """\
``{}``
========================

::

"""

try:
    indir = os.path.dirname(__file__)
except NameError:
    indir = os.getcwd()

apps = [
    'AssignApp',
    'AutogradeApp',
    'CollectApp',
    'ExtensionApp',
    'FeedbackApp',
    'FetchApp',
    'FormgradeApp',
    'ListApp',
    'NbGraderApp',
    'ReleaseApp',
    'SubmitApp',
    'ValidateApp'
]

orig_stdout = sys.stdout
for app in apps:
    cls = getattr(nbgrader.apps, app)
    buf = sys.stdout = StringIO()
    cls().print_help()
    buf.flush()
    helpstr = buf.getvalue()
    helpstr = "\n".join(["    " + x for x in helpstr.split("\n")])

    name = cls.name.replace(" ", "-")
    destination = os.path.join(indir, 'source/command_line_tools/{}.rst'.format(name))
    with open(destination, 'w') as f:
        f.write(header.format(cls.name.replace("-", " ")))
        f.write(helpstr)
