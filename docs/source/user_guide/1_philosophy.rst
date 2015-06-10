
The philosophy and the approach
===============================

nbgrader makes a few assumptions about how the files for your
assignments are organized. By default, nbgrader assumes that your
assignments will be organized with the following directory structure:

::

    {nbgrader_step}/{student_id}/{assignment_id}/{notebook_id}.ipynb

Each subcommand of nbgrader (e.g. ``assign``, ``autograde``, etc.) has
different input and output folders associated with it. These correspond
to the ``nbgrader_step`` variable -- for example, the default input step
directory for ``nbgrader autograde`` is "submitted", while the default
output step directory is "autograded".

The other variables are more self-explanatory: ``student_id``
corresponds to the unique ID of a student, ``assignment_id`` corresponds
to the unique name of an assignment, and ``notebook_id`` corresponds to
the name of a notebook within an assignment (excluding the .ipynb
extension).

Example
-------

Taking the autograde step as an example, when we run the command
``nbgrader autograde "Problem Set 1"``, nbgrader will look for all
notebooks that match the following path:

::

    submitted/*/Problem Set 1/*.ipynb

For each notebook that it finds, it will extract the ``student_id``,
``assignment_id``, and ``notebook_id`` according to the directory
structure described above. It will then autograde the notebook, and save
the autograded version to:

::

    autograded/{student_id}/Problem Set 1/{notebook_id}.ipynb

where ``student_id`` and ``notebook_id`` were parsed from the input file
path.
