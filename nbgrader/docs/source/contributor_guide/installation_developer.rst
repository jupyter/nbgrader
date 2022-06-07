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

Installing Jupyter labextensions
--------------------------------
The labextensions are compiled during installation, and should be in the ``nbgrader/labextension`` directory.
There are 5 of them (*formgrader*, *assignment list*, *course list*, *validate assignment* and *create assignment*),
and with the exception of *create assignment* they must be installed along with the server extensions.

To install the server extensions all together run::

    jupyter server extension enable nbgrader --sys-prefix

It is possible to enable only some of them by running::

    jupyter server extension enable nbgrader.server_extensions.formgrader --sys-prefix
    jupyter server extension enable nbgrader.server_extensions.assignment_list --sys-prefix
    jupyter server extension enable nbgrader.server_extensions.course_list --sys-prefix
    jupyter server extension enable nbgrader.server_extensions.validate_assignment --sys-prefix

To install labextensions run::

    jupyter labextension install .

or in developer mode::

    jupyter labextension develop --overwrite .

Installing classic notebook extensions
--------------------------------------
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
To run tests on nbextensions while developing nbgrader and its documentation, the Firefox headless webdriver must be installed. Please `follow the Mozilla installation instructions <https://developer.mozilla.org/en-US/docs/Web/WebDriver>`_ to get Firefox properly setup on your system.
