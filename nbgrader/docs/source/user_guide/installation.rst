
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

To install and enable both frontend nbextensions (*assignment list* and
*create assignment*) run:

	# The nbextensions are JavaScript/HTML/CSS so they require
	# separate installation and enabling.
    jupyter nbextension install --sys-prefix --py nbgrader
    jupyter nbextension enable --sys-prefix --py nbgrader
    
To install the server extension for *assignment_list* run:

	# The serverextension is a Python module inside nbgrader, so only an
	# enable step is needed.
    jupyter serverextension enable --sys-prefix --py nbgrader

To work properly, the *assignment list* extension requires both the 
nbextension and serverextension. The *create assignment* extension only 
has an nbextension part.

When run in this way with the ``--sys-prefix`` option, the nbextensions and
serverextension will be installed and enabled for anyone using the particular
Python installation or conda env where nbgrader is installed. If that Python
installation is available system-wide, all users will immediately be able to
use the nbgrader extensions. 

There are a number of ways you may need to customize the installation.

First, to install or enable the nbextensions/serverextension for just the
current user, replace ``--sys-prefix`` by ``--user`` in any of the above
commands.

Second, to install or enable the nbextensions/serverextension for all
Python installations on the system, replace ``--sys-prefix`` by ``--system``
in any of the above commands.

Previous versions of nbgrader required each user on a system to enable the
nbextensions; this is no longer needed if the ``--sys-prefix`` option is used
for a system-wide python or the ``--system`` option is used.

Third, you may want to only install one of the nbextensions. To do this, follow
the above steps to install everything and then disable the extension you don't
need using:

	jupyter nbextension disable --sys-prefix assignment_list/main
	
or:

	jupyter nbextension disable --sys-prefix create_assignment/main


Finally, for further documentation on these commands run:

	jupyter nbextension --help-all
	jupyter serverextension --help-all

For advanced instructions on installing the *assignment list* extension please
see the :ref:`advanced installation instructions<assignment-list-installation>`.

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
