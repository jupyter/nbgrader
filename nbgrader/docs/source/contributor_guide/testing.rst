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

    python tasks.py tests

Running selective groups of tests
---------------------------------
To run a selective group of tests you can use one of the following commands:

+------------------------------------------------+------------------------------------+
|  Command                                       | Task                               |
+================================================+====================================+
| ``python tasks.py tests --group=python``       | Run tests only for the Python code |
+------------------------------------------------+------------------------------------+
| ``python tasks.py tests --group=nbextensions`` | Run tests only for the notebook    |
|                                                | extensions                         |
+------------------------------------------------+------------------------------------+
| ``python tasks.py tests --group=docs``         | Build the docs                     |
+------------------------------------------------+------------------------------------+
| ``python tasks.py tests --group=all``          | Same as ``python tasks.py tests``  |
+------------------------------------------------+------------------------------------+

Using pytest to run a single test module
-----------------------------------------
If you want to choose an even more specific subset of tests, you should run
``pytest`` directly. For example, to run only the tests for
``nbgrader generate_assignment``::

    pytest nbgrader/tests/apps/test_nbgrader_assign.py
