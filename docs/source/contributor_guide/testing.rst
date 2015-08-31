Testing
=======

Before making a PR, please run the test suite locally and make sure everything passes.
We have automatic tests on Travis CI, but they take a long time to run and sometimes randomly time out, so it will be much more efficient if you can test locally first.

Running the full test suite
---------------------------
To run the full test suite, run the following command from the root of the repository:

    invoke tests

Running selective groups of tests
---------------------------------
To run only the tests for the Python code, run `invoke tests --group=python`.
To run only the JavaScript tests (e.g. for the notebook extension and the formgrader), run `invoke tests --group=js`.
Note that if you are using Python 3, some of the JavaScript tests will expect that [JupyterHub](https://github.com/jupyter/jupyterhub) is installed.
If you don't want or need to run the JupyterHub tests, you can run the invoke command with `--skip=jupyterhub`.

Using py.test to run a single test module
-----------------------------------------
If you want to choose an even more specific subset of tests, you should invoke `py.test` directly.
For example, to run only the tests for `nbgrader assign`:

    py.test nbgrader/tests/apps/test_nbgrader_assign.py
