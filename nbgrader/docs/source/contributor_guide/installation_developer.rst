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

    pip install -e ".[dev,docs,tests]"

Installing Jupyter labextensions
--------------------------------
The labextensions are compiled during installation, and should be in the ``nbgrader/labextension`` directory.
There are 5 of them (*formgrader*, *assignment list*, *course list*, *validate assignment* and *create assignment*).

All of the labextensions and server extensions are automatically installed and
enabled when installing ``nbgrader``.

To install lab extension in developer mode::

    jupyter labextension develop --overwrite .
