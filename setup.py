#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
from setuptools import setup

# get paths to all the extension files
extension_files = []
for (dirname, dirnames, filenames) in os.walk("nbgrader/nbextensions"):
    root = os.path.relpath(dirname, "nbgrader")
    for filename in filenames:
        if filename.endswith(".pyc"):
            continue
        extension_files.append(os.path.join(root, filename))

# get paths to all the docs
docs_files = []
for (dirname, dirnames, filenames) in os.walk("nbgrader/docs"):
    root = os.path.relpath(dirname, "nbgrader")
    if root.startswith(os.path.join("docs", "build")):
        continue
    if "__pycache__" in root:
        continue
    for filename in filenames:
        if filename.endswith(".pyc"):
            continue
        docs_files.append(os.path.join(root, filename))

# get paths to all the static files and templates
static_files = []
for (dirname, dirnames, filenames) in os.walk("nbgrader/server_extensions/formgrader/static"):
    root = os.path.relpath(dirname, "nbgrader/server_extensions/formgrader")
    for filename in filenames:
        static_files.append(os.path.join(root, filename))
for (dirname, dirnames, filenames) in os.walk("nbgrader/server_extensions/formgrader/templates"):
    root = os.path.relpath(dirname, "nbgrader/server_extensions/formgrader")
    for filename in filenames:
        static_files.append(os.path.join(root, filename))

# get paths to all the alembic files
alembic_files = ["alembic.ini"]
for (dirname, dirnames, filenames) in os.walk("nbgrader/alembic"):
    root = os.path.relpath(dirname, "nbgrader")
    for filename in filenames:
        if filename.endswith(".pyc"):
            continue
        alembic_files.append(os.path.join(root, filename))

setup_args = dict(
    package_data={
        'nbgrader': extension_files + docs_files + alembic_files,
        'nbgrader.nbgraderformat': ["*.json"],
        'nbgrader.server_extensions.formgrader': static_files,
        'nbgrader.tests': [
            'apps/files/*',
            'nbextensions/files/*',
            'preprocessors/files/*'
        ]
    }
)

if __name__ == "__main__":
    setup(**setup_args)
