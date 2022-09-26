# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Custom build target that bails if NBGRADER_NO_LAB is set
import glob
import json
import os
import subprocess

from hatch_jupyter_builder import npm_builder


def builder(target_name, version, *args, **kwargs):

    if os.getenv("NBGRADER_NO_LAB"):
        return

    npm_builder(target_name, version, *args, **kwargs)
