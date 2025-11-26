JavaScript dependencies
=======================

For the time being, we are committing JavaScript dependencies to the formgrader server
extension, as that makes installation much easier.

Adding or updating JavaScript libraries
---------------------------------------
If you need to add a new library, or update the version of a library, you will
need to have `jupyterlab` installed (it provides the `jlpm` command).

Modify the ``package.json`` file in ``nbgrader/server_extensions/formgrader/static/``
and then run::

    python tasks.py js

This will download and install the correct versions of the dependencies to
``nbgrader/server_extensions/formgrader/static/node_modules``.
Usually, JavaScript libraries installed in this way include a lot of extra files
(e.g. tests, documentation) that we don't want to commit to the nbgrader
repository. If this is the case, please add these files to the
``.gitignore`` file so these extra files are ignored and don't get
committed.
