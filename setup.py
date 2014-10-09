#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Juptyer Development Team.
# Distributed under the terms of the Modified BSD License.

from distutils.core import setup

release_info = {}
with open('nbgrader/release.py', 'r') as f:
    code = compile(f.read(), "nbgrader/release.py", 'exec')
    exec(code, release_info)
release_info = {k: v for k, v in release_info.items() if not k.startswith('_')}

setup(packages=['nbgrader'],
      package_data={'': ['templates/*.tpl']},
      scripts=['scripts/nbgrader'],
      **release_info)
