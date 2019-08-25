#!/usr/bin/env python
"""Builds a python package sdist release for upload to pypi.

Usage:

    python tools/release.py

"""

import subprocess as sp
import os
import tempfile
import shutil

def run(cmd, capture=False, **kwargs):
    print(" ".join(cmd))
    if capture:
        proc = sp.Popen(cmd, stdout=sp.PIPE, **kwargs)
    else:
        proc = sp.Popen(cmd, **kwargs)

    stdout, _ = proc.communicate()
    code = proc.wait()
    if code != 0:
        raise RuntimeError("command exited with code {}".format(code))

    if stdout:
        return stdout.decode('utf-8')

# Convert the README to rst
readme = run(["pandoc", "--from", "markdown", "--to", "rst", "README.md"], capture=True)
print("Writing README")
with open("README", "w") as fh:
    fh.write(readme)

# Build the source distribution package
run(["python", "setup.py", "sdist"])
