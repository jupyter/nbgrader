#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

from distutils.core import setup

setup(
    name                = 'nbgrader',
    version             = '0.1',
    description         = 'A system for assigning and grading notebooks',
    author              = 'Jupyter Development Team',
    author_email        = 'ipython-dev@scipy.org',
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
        'nbgrader.html',
        'nbgrader.preprocessors',
        'nbgrader.tests'
    ],
    package_data={
        '': [
            'nbextensions/*.js',
            'nbextensions/*.css'
        ],
        'nbgrader.html': [
            'static/css/*.css',
            'static/css/*.map',
            'static/fonts/*',
            'static/js/*.js',
            'static/lib/*.js',
            'static/lib/*.map',
            'templates/*.tpl',
        ],
        'nbgrader.tests': [
            'files/*',
            'js/*'
        ]
    },
    scripts = ['scripts/nbgrader']
)

