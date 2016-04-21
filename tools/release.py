#!/usr/bin/env python
"""Builds a python package sdist release for upload to pypi.

Usage:

    python tools/release.py

"""

import subprocess as sp

# convert the README to rst
cmd = ["pandoc", "--from", "markdown", "--to", "rst", "README.md"]
print(" ".join(cmd))
proc = sp.Popen(cmd, stdout=sp.PIPE)
stdout = proc.communicate()[0].decode('utf-8')
if proc.wait() != 0:
    raise RuntimeError("pandoc exited with non-zero exit code")

print("Writing README")
with open("README", "w") as fh:
    fh.write(stdout)

# Build the source distribution package
cmd = ["python", "setup.py", "sdist"]
print(" ".join(cmd))
sp.call(cmd)
