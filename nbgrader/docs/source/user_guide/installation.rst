
Installation
============

The nbgrader system and command line tools
------------------------------------------
You may install the current version of nbgrader which includes the grading
system and command line tools::

    pip install nbgrader

Or, if you use `Anaconda <https://www.continuum.io/downloads>`__::

    conda install -c jhamrick nbgrader

nbgrader extensions
-------------------
You may then install the nbgrader extensions for Jupyter notebook. This will
install both the *create assignment* toolbar extension and *assignment list*
notebook server extension::

    nbgrader extension install

To use the toolbar extension as either an instructor or a student, activate the
extension with::

    nbgrader extension activate

If you want to install the extension for only your user environment and not
systemwide, use ``nbgrader extension install --user``. If you don't want to
have to reinstall the extension when nbgrader is updated, use ``nbgrader
extension install --symlink``. If you want to only install a specific
extension, use ``nbgrader extension install <name>``, where ``<name>`` is the
name of the extension you want (e.g. ``create_assignment``).

To get help and see all the options you can pass while installing or activating
the nbgrader notebook extension, use::

    nbgrader extension install --help-all
    nbgrader extension activate --help-all

Quick start
-----------

To get up and running with nbgrader quickly, you can create an example
directory with example course files in it by running the ``nbgrader
quickstart`` command::

    nbgrader quickstart course_id

Where you should replace ``course_id`` with the name of your course. For
further details on how the quickstart command works, please run:

    nbgrader quickstart --help

For an explanation of how this directory is arranged, and what the different
files are in it, continue reading on in :doc:`philosophy`.
