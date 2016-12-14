Testing
=======

Before making a PR, please run the test suite locally and make sure everything
passes.

We have automatic tests on Travis CI, but they take a long time to run and
sometimes randomly time out, so it will be much more efficient if you can
test locally first.

Running the full test suite
---------------------------
To run the full test suite, run the following command from the root of the
repository::

    invoke tests

Running selective groups of tests
---------------------------------
To run a selective group of tests you can use one of the following invoke
commands:

+---------------------------------------+------------------------------------+
|  Command                              | Task                               |
+=======================================+====================================+
| ``invoke tests --group=python``       | Run tests only for the Python code |
+---------------------------------------+------------------------------------+
| ``invoke tests --group=formgrader``   | Run tests only for the formgrader  |
|                                       | app                                |
+---------------------------------------+------------------------------------+
| ``invoke tests --group=nbextensions`` | Run tests only for the notebook    |
|                                       | extensions                         |
+---------------------------------------+------------------------------------+
| ``invoke tests --group=docs``         | Build the docs and check spelling  |
+---------------------------------------+------------------------------------+
| ``invoke tests --group=all``          | Same as ``invoke tests``           |
+---------------------------------------+------------------------------------+

Note that any tests that involve `JupyterHub
<https://github.com/jupyter/jupyterhub>`_ will be skipped if it is not
installed. If, however, you are using Python 3 and have `JupyterHub
<https://github.com/jupyter/jupyterhub>`_ installed and you don't want or need
to run the JupyterHub tests, you can run the invoke command with
``--skip=jupyterhub``.

Using py.test to run a single test module
-----------------------------------------
If you want to choose an even more specific subset of tests, you should invoke
``py.test`` directly. For example, to run only the tests for
``nbgrader assign``::

    py.test nbgrader/tests/apps/test_nbgrader_assign.py
