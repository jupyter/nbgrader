#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import os
from distutils.core import setup
from os.path import join

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
    ],
    packages=[
        'nbgrader',
        'nbgrader.apps',
        'nbgrader.auth',
        'nbgrader.formgrader',
        'nbgrader.preprocessors',
        'nbgrader.tests'
    ],
    package_data={
        'nbgrader': [
            'nbextensions/nbgrader/*.js',
            'nbextensions/nbgrader/*.css'
        ],
        'nbgrader.formgrader': static_files,
        'nbgrader.tests': [
            'files/*',
        ]
    },
    scripts = ['scripts/nbgrader']
)

# setuptools requirements
if 'setuptools' in sys.modules:
    setup_args['install_requires'] = install_requires = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            req = line.strip()
            if not req or req.startswith(('-e', '#')):
                continue
            install_requires.append(req)

setup(**setup_args)