#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from setuptools import setup
from jupyter_packaging import create_cmdclass


def get_data_files():
    """Get the data files for the package."""
    data_files = [
        ("etc/jupyter/jupyter_server_config.d", "etc/jupyter/jupyter_server_config.d/", "*.json"),
        ("etc/jupyter", "etc/jupyter/", "*.json"),
    ]
    return data_files


cmdclass = create_cmdclass(data_files_spec=get_data_files())

setup_args = dict(
    cmdclass=cmdclass
)

if __name__ == "__main__":
    setup(**setup_args)
