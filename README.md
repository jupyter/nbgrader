# nbgrader

[![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter)
[![Build Status](https://travis-ci.org/jupyter/nbgrader.svg?branch=master)](https://travis-ci.org/jupyter/nbgrader)
[![codecov.io](http://codecov.io/github/jupyter/nbgrader/coverage.svg?branch=master)](http://codecov.io/github/jupyter/nbgrader?branch=master)

A system for assigning and grading Jupyter notebooks.

[Documentation can be found on Read the Docs.](http://nbgrader.readthedocs.org)


## Visual highlights of nbgrader

### Instructor toolbar extension for Jupyter notebooks
The nbgrader toolbar extension for Jupyter notebooks guides the instructor through
assignment and grading tasks using the familiar Jupyter notebook interface.

![Creating assignment](docs/source/user_guide/images/creating_assignment.gif "Creating assignment")

### Student assignment list extension for Jupyter notebooks
Using the assignment list extension, students may conveniently view, fetch,
submit, and validate their assignments.

![nbgrader assignment list](docs/source/user_guide/images/student_assignment.gif "nbgrader assignment list")

### The command line tools of nbgrader
[Command line tools](https://nbgrader.readthedocs.org/en/stable/command_line_tools/index.html)
offer an efficient way for the instructor to generate, assign, release, collect,
and grade notebooks.

* `nbgrader assign`: create a student version of a notebook
* `nbgrader release`: release a notebook to students
* `nbgrader collect`: collect students' submissions
* `nbgrader autograde`: autograde students' submissions
* `nbgrader formgrade`: launch the formgrader


## Installation
You may install the current version of nbgrader which includes the grading
system and command line tools using:

    pip install nbgrader
    
For detailed instructions on installing nbgrader and the nbgrader extensions
for Jupyter notebook, please see [Installation](https://nbgrader.readthedocs.org/en/stable/user_guide/01a_installation.html)
section in the User Guide.


## Contributing
Please see the [contributing guidelines and documentation](CONTRIBUTING.md).

If you want to develop features for nbgrader, please follow the
[development installation instructions](CONTRIBUTING.md#development-installation).
