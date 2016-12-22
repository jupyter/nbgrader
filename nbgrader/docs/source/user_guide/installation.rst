
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

You may then install the nbgrader extensions for Jupyter notebook. Previously
this was done using the ``nbgrader extension install`` command. However, moving
forward this is done using the ``jupyter nbextension`` and ``jupyter serverextension``
commands.

To install and enable the frontend nbextensions (*assignment list* and
*create assignment*) run:

    jupyter nbextension install --sys-prefix --py nbgrader
    jupyter nbextension enable --sys-prefix --py nbgrader
    
To install the server extension for *assignment_list* run:

    jupyter serverextension enable --sys-prefix --py nbgrader

In both the ``nbextension`` and ``serverextension`` commands:

* To install for all users, replace `--sys-prefix` by `--system`.
* To install only for the current user replace `--sys-prefix` by `--user`.

If you don't want to have to reinstall the nbextension when nbgrader is updated, add
``--symlink`` to the ``nbextension`` command.

For further documentation on these commands run:

	jupyter nbextension --help-all
	jupyter serverextension --help-all

For instructions on installing the "Assignment List" extension for all users in
a shared server setup, please see the :ref:`advanced installation instructions
<assignment-list-installation>`.

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
