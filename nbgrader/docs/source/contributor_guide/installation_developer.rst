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
Building nbgrader jupyterlab extension requires nodejs to be installed.
We recommand using `conda environment <https://docs.conda.io/en/latest/miniconda.html>`_ with `mamba <https://mamba.readthedocs.io/en/latest/>`_::

    # create a new environment
    mamba create -n nbgrader -c conda-forge python nodejs -y

    # activate the environment
    mamba activate nbgrader

    pip install -e ".[docs,tests]"

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
*create assignment*, and *formgrader*) and the frontend labextensions
along with the server extensions (*assignment list* and *formgrader*) run::

    jupyter labextension develop --overwrite .
    jupyter nbextension install --symlink --sys-prefix --py nbgrader
    jupyter nbextension enable --sys-prefix --py nbgrader
    jupyter serverextension enable --sys-prefix --py nbgrader

To work properly, the *assignment list* and *formgrader* extensions require
both the frontend extension and serverextension. The *create assignment* extension
only has an frontend extension part.

Installing Firefox Headless WebDriver
-------------------------------------
To run tests while developing nbgrader and its documentation, the Firefox headless webdriver must be installed. Please `follow the Mozilla installation instructions <https://developer.mozilla.org/en-US/docs/Web/WebDriver>`_ to get Firefox properly setup on your system.
