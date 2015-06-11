#!/usr/bin/env python

import os.path
from nbgrader.apps import NbGraderApp

header = """\
Configuration options
=====================

These options can be set in ``nbgrader_config.py``, or at the command line when you start it.
::

"""

try:
    indir = os.path.dirname(__file__)
except NameError:
    indir = os.getcwd()

config = NbGraderApp().generate_config_file()
config = "\n".join(["    " + x for x in config.split("\n")])
destination = os.path.join(indir, 'source/config_options.rst')
with open(destination, 'w') as f:
    f.write(header)
    f.write(config)
