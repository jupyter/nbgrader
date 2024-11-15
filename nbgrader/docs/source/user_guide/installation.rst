
Installation
============

The nbgrader system and command line tools
------------------------------------------
You may install the current version of nbgrader which includes the grading
system and command line tools::

    pip install nbgrader

Or, if you use `Anaconda <https://www.anaconda.com/download>`__::

    conda install jupyter
    conda install -c conda-forge nbgrader


nbgrader extensions in Jupyter Lab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extensions will be automatically installed after the installation of nbgrader.

The installation will activated 4 server extensions
(formgrader, assignment_list, course_list and validate_assignment)
and 5 labextensions (formgrader, assignment-list, course-list, validate-assignment and create-assignment).

The server extensions can be disabled individually by running::

    jupyter server extension disable nbgrader.server_extensions.formgrader
    jupyter server extension disable nbgrader.server_extensions.assignment_list
    jupyter server extension disable nbgrader.server_extensions.course_list
    jupyter server extension disable nbgrader.server_extensions.validate_assignment

The labextensions are all enabled by default, but can be disabled individually by running::

    jupyter labextension disable @jupyter/nbgrader:formgrader
    jupyter labextension disable @jupyter/nbgrader:assignment-list
    jupyter labextension disable @jupyter/nbgrader:course-list
    jupyter labextension disable @jupyter/nbgrader:create-assignment
    jupyter labextension disable @jupyter/nbgrader:validate-assignment

or enabled::

    jupyter labextension enable @jupyter/nbgrader:formgrader
    jupyter labextension enable @jupyter/nbgrader:assignment-list
    jupyter labextension enable @jupyter/nbgrader:course-list
    jupyter labextension enable @jupyter/nbgrader:create-assignment
    jupyter labextension enable @jupyter/nbgrader:validate-assignment

To work properly, the **assignment list**, **formgrader**, **course list** and **validate assignment**
extensions require both the labextension and server extension. The **create
assignment** extension only has an labextension part.

Installation options
~~~~~~~~~~~~~~~~~~~~

When installed/enabled with the ``--sys-prefix`` option, the
server extension will be installed and enabled for anyone using the particular
Python installation or conda environment where nbgrader is installed. If that
Python installation is available system-wide, all users will immediately be
able to use the nbgrader extensions.

There are a number of ways you may need to customize the installation:

-  To install or enable the labextensions/server extension for just the
   current user, run the above commands with ``--user`` instead of ``--sys-prefix``::

    jupyter labextension enable --level=user @jupyter/nbgrader
    jupyter server extension enable --user --py nbgrader

-  To install or enable the labextensions/server extension for all
   Python installations on the system, run the above commands with ``--system`` instead of ``--sys-prefix``::

    jupyter labextension enable --level=system @jupyter/nbgrader
    jupyter server extension enable --system --py nbgrader

Disabling extensions
~~~~~~~~~~~~~~~~~~~~

You may want to only install one of the nbgrader extensions. To do this, follow
the above steps to install everything and then disable the extension you don't
need. For example, to disable the Assignment List extension::

    jupyter labextension disable --level=sys_prefix @jupyter/nbgrader:assignment-list
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.assignment_list

or to disable the Create Assignment extension::

    jupyter labextension disable --level=sys_prefix @jupyter/nbgrader:create-assignment

or to disable the Formgrader extension::

    jupyter labextension disable --level=sys_prefix @jupyter/nbgrader:formgrader
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.formgrader

or to disable the Course List extension::

    jupyter labextension disable --level=sys_prefix @jupyter/nbgrader:course-list
    jupyter server extension disable --sys-prefix nbgrader.server_extensions.course_list

For example lets assume you have installed nbgrader via `Anaconda
<https://www.anaconda.com/download>`__ (meaning all serverextensions are installed
and enabled with the ``--sys-prefix`` flag, i.e. anyone using the particular
Python installation or conda environment where nbgrader is installed). But you
only want the *create assignment* extension available to a specific user and
not everyone else. First you will need to disable the *create assignment*
extension for everyone else::

    jupyter labextension disable @jupyter/nbgrader:create-assignment

Log in with the specific user and then enable the *create assignment* extension
only for that user::

    jupyter labextension enable --level=user @jupyter/nbgrader:create-assignment

Finally to see all installed labextensions/server extensions, run::

    jupyter labextension list
    jupyter server extension list

For further documentation on these commands run::

    jupyter labextension --help-all
    jupyter server extension --help-all

For advanced instructions on installing the *assignment list* extension please
see the :ref:`advanced installation instructions<assignment-list-installation>`.

Quick start
-----------

To get up and running with nbgrader quickly, you can create an example
directory with example course files in it by running the ``nbgrader
quickstart`` command::

    nbgrader quickstart course_id

Where you should replace ``course_id`` with the name of your course. For
further details on how the quickstart command works, please run::

    nbgrader quickstart --help

For an explanation of how this directory is arranged, and what the different
files are in it, continue reading on in :doc:`philosophy`.
