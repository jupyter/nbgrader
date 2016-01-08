Installation
============

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
Install the notebook extensions. The ``--symlink`` option is recommended since it
updates the extensions whenever you update the nbgrader repository. Finally,
activate the notebook extensions::

    nbgrader extension install --symlink
    nbgrader extension activate

Installing Phantomjs
--------------------
To run tests while developing nbgrader and its documentation, Phantomjs must
be installed.

Install using npm
~~~~~~~~~~~~~~~~~
If you have npm installed, you can install phantomjs using::

    npm install phantomjs

Install using other package managers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you do not have npm installed, you can still install phantomjs.

On OS X::

    brew update
    brew install phantomjs

On Linux::

    apt-get update
    apt-get install phantomjs
