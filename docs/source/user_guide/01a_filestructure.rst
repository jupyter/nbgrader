
Recommended file structure
==========================
For instructor ease of use and developer maintenance, nbgrader makes a few
assumptions about how your assignment files are organized. By default, nbgrader
assumes that your assignments will be organized with the following directory
structure:

::

    {course_directory}/{nbgrader_step}/{student_id}/{assignment_id}/{notebook_id}.ipynb

course_directory
----------------
 ``course_directory`` variable is the root directory where you run the nbgrader commands.
  This means that you can place your class files directory wherever you want.
  However, this location can also be customized (see the :doc:`configuration options </config_options>`) so that you can run the nbgrader commands from anywhere on your system, but still have them operate on the same directory.

nbgrader_step
-------------
Each subcommand of nbgrader (e.g. ``assign``, ``autograde``, etc.) has
different input and output folders associated with it. These correspond
to the ``nbgrader_step`` variable -- for example, the default input step
directory for ``nbgrader autograde`` is "submitted", while the default
output step directory is "autograded".

identifiers
-----------
The other variables are more self-explanatory: ``student_id``
corresponds to the unique ID of a student, ``assignment_id`` corresponds
to the unique name of an assignment, and ``notebook_id`` corresponds to
the name of a notebook within an assignment (excluding the .ipynb
extension).

Database of assignments
-----------------------
Additionally, nbgrader needs access to a database to store information about the assignments.
This database is, by default, a sqlite database that lives at ``{course_directory}/gradebook.db``, but you can also configure this to be any location of your choosing.
You do not need to manually create this database yourself, as nbgrader will create it for you, but you probably want to prepopulate it with some information about assignment due dates and students (see :doc:`03_generating_assignments` and :doc:`04_autograding`).
Additionally, nbgrader uses SQLAlchemy, so you should be able to also use MySQL or PostgreSQL backends as well (though in these cases, you *will* need to create the database ahead of time, as this is just how MySQL and PostgreSQL work).


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
