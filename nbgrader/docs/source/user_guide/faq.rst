Frequently asked questions
==========================

.. contents:: Table of contents
   :depth: 2

Can I use nbgrader for purely manually graded assignments (i.e., without autograding)?
--------------------------------------------------------------------------------------------

Yes, absolutely! Mark all the cells where students write their answers as
:ref:`manually-graded-cells` and then during grading run ``nbgrader autograde``
and ``nbgrader formgrade`` as normal. If you don't want to even execute the
notebooks, you can pass the ``--no-execute`` flag to
:doc:`/command_line_tools/nbgrader-autograde`.

Can I hide the test cells in a nbgrader assignment?
---------------------------------------------------

Not at the moment, though it is on the todo list (see `#390
<https://github.com/jupyter/nbgrader/issues/390>`_). :ref:`PRs welcome!
<pull-request>`

How does nbgrader ensure that students do not change the tests?
---------------------------------------------------------------

Please see the documentation on :ref:`read-only-cells`.

Does nbgrader support parallel autograding of assignments?
----------------------------------------------------------

Not yet, though it is on the todo list (see `#174
<https://github.com/jupyter/nbgrader/issues/174>`_). :ref:`PRs welcome!
<pull-request>`

Does nbgrader protect against infinite loops?
---------------------------------------------

Yes. nbgrader will stop executing a cell after a certain period of time. This
timeout is customizable through the ``ExecutePreprocessor.timeout``
configuration option. See :doc:`/configuration/config_options`.

Does nbgrader protect against unsafe code?
-------------------------------------------

Not yet, though it is on the todo list (see `#483
<https://github.com/jupyter/nbgrader/issues/483>`_). :ref:`PRs welcome!
<pull-request>`

How does nbgrader handle late assignments?
------------------------------------------

By default nbgrader won't explicitly assign late penalties, but it will
compute how late each submission is. If you wish to customize this default
behavior see :doc:`adding customization plugins </plugins/index>`

For this to work, you must include a duedate for the assignment and then a
``timestamp.txt`` file in the folder for each submission with a single line
containing a timestamp (e.g. ``2015-02-02 14:58:23.948203 PST``). Then, when
you run ``nbgrader autograde``, nbgrader will record these timestamps into the
database. You can access the timestamps through the API, like so::

    from nbgrader.api import Gradebook
    gb = Gradebook("sqlite:///gradebook.db")
    assignment = gb.find_assignment("ps1")
    for submission in assignment.submissions:
        print("Submission from '{}' is {} seconds late".format(
            submission.student_id, submission.total_seconds_late))

Note that if you use the release/fetch/submit/collect commands (see
:doc:`managing_assignment_files`), the ``timestamp.txt`` files will be included
automatically.

Do I have to use sqlite for the nbgrader database?
--------------------------------------------------

No, and in fact, if you have multiple people grading accessing the formgrader
at the same time we strongly encourage you **not** to use sqlite because it is
not threadsafe. Postgres is also supported, and anything else that works with
SQLAlchemy is likely to work (e.g. MySQL), though only sqlite and Postgres have
been tested. If you want to use another SQL-based database and find that it
doesn't work for some reason, please `open an issue
<https://github.com/jupyter/nbgrader/issues/new>`_!

Does nbgrader work with non-Python kernels?
-------------------------------------------

Yes, though it hasn't been extensively tested with other kernels and it is
likely there are some edge cases where things do not work quite right. If you
run into any issues using nbgrader with other kernels, please
`open an issue <https://github.com/jupyter/nbgrader/issues/new>`_!
