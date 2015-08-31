Installation for Contributors
=============================

Dependencies
------------

Phantomjs must be installed in order to run tests.
If you have npm installed, you can install phantomjs using:

    npm install phantomjs

If you do not have npm installed, you can still install phantomjs.
On OS X:

    brew update
    brew install phantomjs

On Linux:

    apt-get update
    apt-get install phantomjs


Installing nbgrader from source
-------------------------------

To develop and test nbgrader, you will want to install nbgrader from source.
First, clone the git repository:

    git clone https://github.com/jupyter/nbgrader
    cd nbgrader

Then, you must install nbgrader using [flit](https://github.com/takluyver/flit) (note that flit requires Python 3):

    pip3 install flit
    flit install --symlink

You will probably also want to install the notebook extension using a symlink, so that it updates whenever you update the repository:

    nbgrader extension install --symlink
    nbgrader extension activate
