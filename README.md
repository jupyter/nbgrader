# nbgrader

[![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter)
[![Build Status](https://travis-ci.org/jupyter/nbgrader.svg)](https://travis-ci.org/jupyter/nbgrader)
[![Coverage Status](https://coveralls.io/repos/jupyter/nbgrader/badge.svg)](https://coveralls.io/r/jupyter/nbgrader)

A system for assigning and grading notebooks.

**Warning: nbgrader is not yet stable and is under active development. The following instructions are currently incomplete and may change!**

[Documentation can be found on Read the Docs.](http://nbgrader.readthedocs.org)

## Installation

Developers can install a development version following the instructions in the [contributing guidelines and documentation](CONTRIBUTING.md). All other users can install using the instructions below:

To install the most recent (development, and possibly unstable!) version of nbgrader, run:

```bash
pip install git+git://github.com/jupyter/nbgrader.git@master
```

You can then install and activate the nbgrader assignment toolbar extension with:

```bash
nbgrader extension install
nbgrader extension activate
```

If you want to install the extension for only yourself (and not systemwide), use `nbgrader extension install --user`. If you don't want to have to reinstall the extension when nbgrader is updated, use `nbgrader extension install --symlink`. To get help and see all the options you can pass while installing/activating the nbgrader notebook extension, use:

```bash
nbgrader extension install --help-all
nbgrader extension activate --help-all
```

## Contributing

Please see the [contributing guidelines and documentation](CONTRIBUTING.md).
