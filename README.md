# nbgrader

[![Gitter chat](https://badges.gitter.im/jupyter/nbgrader.png)](https://gitter.im/jupyter/nbgrader)
[![Build Status](https://travis-ci.org/jupyter/nbgrader.svg)](https://travis-ci.org/jupyter/nbgrader)
[![Coverage Status](https://coveralls.io/repos/jupyter/nbgrader/badge.svg)](https://coveralls.io/r/jupyter/nbgrader)

A system for assigning and grading notebooks.

**Warning: nbgrader is not yet stable and is under active development. The following instructions are currently incomplete and may change!**

[Documentation can be found on nbviewer.](http://nbviewer.ipython.org/github/jupyter/nbgrader/tree/docs/Index.ipynb)

## Dependencies

To install nbgrader, you will need version 3.x of IPython. However, note that version 3.0 will **NOT** work -- you will need at least version 3.1. If you do not have version 3.1 of IPython installed (you can check with `ipython --version`), you can install it by:

```bash
git clone --recursive -b 3.x https://github.com/ipython/ipython.git && pip install -e "ipython[all]"
```

## Installation

To install the most recent (development, and possibly unstable!) version of nbgrader, run:

```bash
pip install git+git://github.com/jupyter/nbgrader.git@master
```

You can then install and activate the nbgrader assignment toolbar extension with:

```bash
nbgrader extension install
nbgrader extension activate
```

To get help and see all the options you can pass while installing/activating the nbgrader notebook extension, use:

```bash
nbgrader extension install --help-all
nbgrader extension activate --help-all
```
