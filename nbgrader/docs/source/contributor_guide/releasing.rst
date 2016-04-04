Releasing a new version
=======================

.. caution::
    This piece of documentation is a work-in-progress. Some pieces may be
    missing and what is here may possibly be incorrect.

Building conda packages
-----------------------

The recipe for the nbgrader conda package is located in the `conda.recipe`
folder and should include all the necessary information about dependencies and
version. This should be kept up-to-date with the main `setup.py` in the root of
the repository.

To build the conda packages, you can use the script `conda_build.sh` in the
`tools` directory. This will build a conda package for each supported version
of Python (currently, 2.7, 3.4, and 3.5) and run the full test suite (excluding
JupyterHub tests) in a fresh conda environment. This ensures that all the
necessary package files are actually being installed.

After the packages have been built, the script will convert them for all
available platforms (osx, linux, and windows). Finally, after converting the
packages, they will be uploaded to Anaconda Cloud.