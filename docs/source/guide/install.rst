Installing nbgrader
===================

To install nbgrader, clone the git repository and then run ``python
setup.py install`` from the root of the repository:

.. code:: bash

    git clone https://github.com/jupyter/nbgrader.git
    cd nbgrader
    python setup.py install

To additionally install the assignment toolbar notebook extension:

.. code:: bash

   cp nbextensions/* $(ipython locate)/nbextensions/
