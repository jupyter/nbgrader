
Manually grading a student's solution
=====================================

.. raw:: html

   <div class="alert alert-warning">

For the full documentation on ``nbgrader formgrade`` (including the list
of all configurable options), run ``nbgrader formgrade --help-all``.

.. raw:: html

   </div>

After assignments have been autograded, they will saved into an
``autograded`` directory (see `the philosophy and the
approach <1%20-%20Philosophy.ipynb>`__ for details):

After running ``nbgrader autograde``, the autograded version of the
notebooks will be:

::

    autograded/{student_id}/{assignment_id}/{notebook_id}.ipynb

To grade the assignments with an HTML form, all we have to do is run:

.. code:: bash

    nbgrader formgrade

This will launch a server at ``http://localhost:5000`` that will provide
you with an interface for hand grading assignments that it finds in the
directory listed above. Note that this applies to *all* assignments as
well -- as long as `the autograder <4%20-%20Autograding.ipynb>`__ has
been run on the assignment, it will be available for manual grading via
the formgrader.

The formgrader doesn't actually modify the files on disk at all; it only
modifies information about them in the database. So, there is no
"output" step for the formgrader.
