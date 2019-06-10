The ``nbgrader_config.py`` file
===============================

.. seealso::

    :doc:`config_options`
        A list of all config options for ``nbgrader_config.py``.

The ``nbgrader_config.py`` file is the main place for you to specify options
for configuring nbgrader. Normally, it should be located in the same directory
as where you are running the nbgrader commands, or you can place it in one of a
number of other locations on your system. These locations correspond to the
configuration directories that Jupyter itself looks in; you can find out what
these are by running ``jupyter --paths``.

Things get a bit more complicated in certain setups, so this document aims to clarify how to setup the ``nbgrader_config.py`` file in multiple different scenarios.

Using ``nbgrader_config.py``
----------------------------

To set a configuration option in the config file, you need to use the ``c``
variable which actually stores the config. For example::

    c = get_config()
    c.CourseDirectory.course_id = "course101"

To get an example config file, you can run ``nbgrader generate_config``.


Use Case 1: nbgrader and ``jupyter notebook`` run in the same directory
-----------------------------------------------------------------------

The easiest way to use nbgrader and the formgrader extension is to run both
from the same directory. For example::

    nbgrader quickstart ./course101
    cd ./course101
    jupyter notebook

In this case, there should be a ``nbgrader_config.py`` file in the directory
``./course101``, which corresponds both to the directory where the notebook is
running and the directory where the nbgrader commands will be run.

As mentioned above, you can actually put the ``nbgrader_config.py`` file in any of the directories listed by ``jupyter --paths`` in the "Config" section.


Use Case 2: nbgrader and ``jupyter notebook`` run in separate directories
-------------------------------------------------------------------------

.. warning::

    The nbgrader course directory must be a subdirectory of where you run the
    Jupyter notebook.

A common use case is to run the notebook server from the root of your home
directory, which is likely not the place where you will be running nbgrader
from. In this case, you will need to tell the nbgrader extensions---which run
as part of the notebook server---where to find your course directory. In this
case, you want *two* ``nbgrader_config.py`` files: one for your main course directory (where you run the nbgrader commands) and one that specifies for the notebook where the course directory is.

For example, the ``nbgrader_config.py`` that the notebook knows about could be placed in ``~/.jupyter/nbgrader_config.py``, and it would include a path to where the main course directory is::

    c = get_config()
    c.CourseDirectory.root = "/path/to/course/directory"

Then you would additionally have a config file at ``/path/to/course/directory/nbgrader_config.py``.


Use Case 3: nbgrader and JupyterHub
-----------------------------------

.. seealso::

    :doc:`jupyterhub_config`
        Further information on using nbgrader with JupyterHub.

The setup of ``nbgrader_config.py`` files gets a bit more complicated when you
are running a shared server with JupyterHub. In this case, you will likely need (at least) three separate ``nbgrader_config.py`` files:

1. A global ``nbgrader_config.py`` (for example, placed in a global path like ``/usr/local/etc/jupyter`` or ``/etc/jupyter``, but check ``jupyter --paths`` to see which ones are valid on your system). This global file should include information relevant to all students, instructors, and formgraders, such as the location of the exchange directory.

2. An ``nbgrader_config.py`` that tells the notebook server running the formgrader where the course directory is located (as in Use Case 2). The options in this config file will only be relevant for the formgrader, and not any other user accounts.

3. An ``nbgrader_config.py`` file in the course directory itself. The options in this config file will only be relevant for the formgrader, and not any other user accounts.

