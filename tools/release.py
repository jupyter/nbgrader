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

# Get the version number
version = run(["python", "setup.py", "--version"], capture=True).rstrip()

# Get the current directory
currdir = os.getcwd()

# Create a temporary conda environment
tempdir = tempfile.mkdtemp()
condadir = os.path.join(tempdir, "conda")
run(["conda", "create", "-y", "-p", condadir, "python=3"])
env = os.environ.copy()
env['PATH'] = "{}:{}".format(os.path.join(condadir, "bin"), env['PATH'])

# Install nbgrader into the temporary conda environment and run the tests
try:
    os.chdir(tempdir)
    run(["pip", "install", "-r", os.path.join(currdir, "dev-requirements.txt")], env=env)
    run(["pip", "install", os.path.join(currdir, "dist", "nbgrader-{}.tar.gz".format(version))], env=env)
    run(["python", "-m", "nbgrader.tests", "-v", "-x"], env=env)

finally:
    os.chdir(currdir)
    shutil.rmtree(tempdir)
