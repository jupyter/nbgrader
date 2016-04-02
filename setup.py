#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import os
from distutils.core import setup
from os.path import join

# get paths to all the extension files
extension_files = []
for (dirname, dirnames, filenames) in os.walk("nbgrader/nbextensions"):
    root = os.path.relpath(dirname, "nbgrader")
    for filename in filenames:
        if filename.endswith(".pyc"):
            continue
        extension_files.append(os.path.join(root, filename))

# get paths to all the static files and templates
static_files = []
for (dirname, dirnames, filenames) in os.walk("nbgrader/formgrader/static"):
    root = os.path.relpath(dirname, "nbgrader/formgrader")
    for filename in filenames:
        static_files.append(os.path.join(root, filename))
for (dirname, dirnames, filenames) in os.walk("nbgrader/formgrader/templates"):
    root = os.path.relpath(dirname, "nbgrader/formgrader")
    for filename in filenames:
        static_files.append(os.path.join(root, filename))

name = 'nbgrader'
here = os.path.abspath(os.path.dirname(__file__))
version_ns = {}
with open(join(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)

setup_args = dict(
    name                = name,
    version             = version_ns['__version__'],
    description         = 'A system for assigning and grading notebooks',
    author              = 'Jupyter Development Team',
    author_email        = 'jupyter@googlegroups.com',
    license             = 'BSD',
    url                 = 'https://github.com/jupyter/nbgrader',
    keywords            = ['Notebooks', 'Grading', 'Homework'],
    classifiers         = [
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=[
        'nbgrader',
        'nbgrader.apps',
        'nbgrader.auth',
        'nbgrader.formgrader',
        'nbgrader.preprocessors',
        'nbgrader.tests',
        'nbgrader.tests.api',
        'nbgrader.tests.apps',
        'nbgrader.tests.formgrader',
        'nbgrader.tests.nbextensions',
        'nbgrader.tests.preprocessors',
        'nbgrader.tests.utils'
    ],
    package_data={
        'nbgrader': extension_files,
        'nbgrader.formgrader': static_files,
        'nbgrader.tests': [
            'apps/files/*',
            'nbextensions/files/*',
            'preprocessors/files/*'
        ]
    },
    scripts = ['scripts/nbgrader']
)

setup_args['install_requires'] = install_requires = []
with open('requirements.txt') as f:
    for line in f.readlines():
        req = line.strip()
        if not req or req.startswith(('-e', '#')):
            continue
        install_requires.append(req)

setup(**setup_args)