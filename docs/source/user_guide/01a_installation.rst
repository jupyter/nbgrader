
Installation
============

The nbgrader system and command line tools
------------------------------------------
You may install the current version of nbgrader which includes the grading
system and command line tools::

    pip install nbgrader

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
systemwide, use ``nbgrader extension install --user``.
If you don't want to have to reinstall the extension when nbgrader is updated,
use ``nbgrader extension install --symlink``.

To get help and see all the options you can pass while installing or activating
the nbgrader notebook extension, use::

    nbgrader extension install --help-all
    nbgrader extension activate --help-all
