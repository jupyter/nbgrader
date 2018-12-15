Developer installation
======================

Getting the source code
-----------------------
The source files for nbgrader and its documentation are hosted on GitHub. To
clone the nbgrader repository::

    git clone https://github.com/jupyter/nbgrader
    cd nbgrader

Installing and building nbgrader
-------------------------------------
nbgrader installs and builds with one command::

    pip install -r dev-requirements.txt -e .


Installing notebook extensions
------------------------------
Previously this was done using the ``nbgrader extension install`` command.
However, moving forward this is done using the ``jupyter nbextension`` and
``jupyter serverextension`` commands.

The nbextensions are Javascript/HTML/CSS so they require
separate installation and enabling.
The --symlink option is recommended since it updates the extensions
whenever you update the nbgrader repository.
The serverextension is a Python module inside nbgrader, so only an
enable step is needed.
To install and enable all the frontend nbextensions (*assignment list*,
*create assignment*, and *formgrader*) along with the server extensions
(*assignment list* and *formgrader*) run::

    jupyter nbextension install --symlink --sys-prefix --py nbgrader
    jupyter nbextension enable --sys-prefix --py nbgrader
    jupyter serverextension enable --sys-prefix --py nbgrader

To work properly, the *assignment list* and *formgrader* extensions require
both the nbextension and serverextension. The *create assignment* extension
only has an nbextension part.

Installing Firefox Headless WebDriver
-------------------------------------
To run tests while developing nbgrader and its documentation, the Firefox headless webdriver must be installed. Please `follow the Mozilla installation instructions <https://developer.mozilla.org/en-US/docs/Web/WebDriver>`_ to get Firefox properly setup on your system.
