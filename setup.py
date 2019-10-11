#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

import os
from setuptools import setup, find_packages

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


name = u'nbgrader'
here = os.path.abspath(os.path.dirname(__file__))
version_ns = {}
with open(os.path.join(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)

setup_args = dict(
    name=name,
    version=version_ns['__version__'],
    description='A system for assigning and grading notebooks',
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    url='https://github.com/jupyter/nbgrader',
    keywords=['Notebooks', 'Grading', 'Homework'],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    package_data={
        'nbgrader': extension_files + docs_files + alembic_files,
        'nbgrader.nbgraderformat': ["*.json"],
        'nbgrader.server_extensions.formgrader': static_files,
        'nbgrader.tests': [
            'apps/files/*',
            'nbextensions/files/*',
            'preprocessors/files/*'
        ]
    },
    entry_points={
        'console_scripts': ['nbgrader=nbgrader.apps.nbgraderapp:main']
    },
    install_requires=[
        "sqlalchemy",
        "python-dateutil",
        "jupyter",
        "notebook>=4.2",
        "nbconvert>=5.6",
        "nbformat",
        "traitlets>=4.3.3", # see PR #1239
        "jupyter_core",
        "jupyter_client",
        "tornado",
        "six>=1.11",  # jsonschema needs >=1.11
        "requests",
        "jsonschema",
        "alembic",
        "fuzzywuzzy"
    ]
)

if __name__ == "__main__":
    setup(**setup_args)
