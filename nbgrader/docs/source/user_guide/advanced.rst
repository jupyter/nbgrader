Advanced topics
===============

This file covers some more advanced use cases of nbgrader.

.. contents:: Table of contents
   :depth: 2

Running nbgrader with JupyterHub
--------------------------------

Please see :doc:`/configuration/jupyterhub_config`.

.. _getting-information-from-db:

Getting information from the database
-------------------------------------

nbgrader offers a fairly rich :doc:`API </api/index>` for interfacing with the
database. The API should allow you to access pretty much anything you want,
though if you find something that can't be accessed through the API please
`open an issue <https://github.com/jupyter/nbgrader/issues/new>`_!

In this example, we'll go through how to create a CSV file of grades for each
student and assignment using nbgrader and `pandas
<http://pandas.pydata.org/>`__.

.. versionadded:: 0.4.0
    nbgrader now comes with CSV export functionality out-of-the box using the
    :doc:`nbgrader export </command_line_tools/nbgrader-export>` command.
    However, this example is still kept for reference as it may be useful for
    :doc:`defining your own exporter </plugins/export-plugin>`.

.. literalinclude:: extract_grades.py
   :language: python

After running the above code, you should see that ``grades.csv`` contains something that looks like::

    student,assignment,max_score,score
    bitdiddle,ps1,9.0,1.5
    hacker,ps1,9.0,3.0

Using nbgrader preprocessors
----------------------------

Several of the nbgrader preprocessors can be used with nbconvert without
actually relying on the rest of the nbgrader machinery. In particular, the
following preprocessors can be applied to other nbconvert workflows:

- ``ClearOutput`` -- clears outputs of all cells
- ``ClearSolutions`` -- removes solutions between the
  solution delimeters (see :ref:`autograded-answer-cells`).
- ``HeaderFooter`` -- concatenates notebooks together,
  prepending a "header" notebook and/or appending a "footer" notebook to
  another notebook.
- ``LimitOutput`` -- limits the amount of output any given
  cell can have. If a cell has too many lines of outputs, they will be
  truncated.

Using these preprocessors in your own nbconvert workflow is relatively
straightforward. In your ``nbconvert_config.py`` file, you would add, for
example:

.. code:: python

    c.Exporter.preprocessors = ['nbgrader.preprocessors.ClearSolutions']

See also the nbconvert docs on `custom preprocessors <https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html#Custom-Preprocessors>`__.

Calling nbgrader apps from Python
---------------------------------

nbgrader apps themselves can be called directly from Python (rather than
through a subprocess), though **this use case is discouraged** as it is a bit
fragile. In general, if you want to use pieces of nbgrader programmatically we
recommend you use one of the preprocessors (see the previous sections). If this
really won't work for you, read on.

To run nbgrader from Python you need to create an instance of the application.
All the applications have camelcase names without the "nbgrader" part, e.g.
``nbgrader assign`` becomes ``AssignApp``:

.. code:: python

    from nbgrader.apps import AssignApp
    app = AssignApp.instance()

Next, you need to initialize and start the application using arguments, just
like you'd use on the command line:

.. code:: python

    command_line_args = ["ps1", "--force"]
    app.initialize(command_line_args)
    app.start()

Finally, if you want to be able to run the app again, you will need to reset
the application state:

.. code:: python

    app.reset()

Note that some of the apps (such as ``nbgrader validate``) may not work
correctly when used this way. Use at your own risk!
