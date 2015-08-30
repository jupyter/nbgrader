
Manually grading a student's solution
=====================================

.. seealso::

    :doc:`/command_line_tools/nbgrader-formgrade`
        Command line options for ``nbgrader formgrade``

    :doc:`01_philosophy`
        More details on how the nbgrader hierarchy is structured.

    :doc:`/config_options`
        Details on ``nbgrader_config.py``

After assignments have been autograded, they will saved into an
``autograded`` directory (see :doc:`01_philosophy` for details):

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
well -- as long as :doc:`the autograder <04_autograding>` has
been run on the assignment, it will be available for manual grading via
the formgrader.

The formgrader doesn't actually modify the files on disk at all; it only
modifies information about them in the database. So, there is no
"output" step for the formgrader.

Important note: if you run the formgrader on a public IP address and port (for example, by running ``nbgrader formgrade --ip=<public_ip>``), then *anyone* will be able to access the formgrader at its URL!
So, you probably want to only run the formgrader on a private network that only the instructors have access to (e.g., behind a VPN).
Alternately, if students are accessing their notebooks via JupyterHub, then you can configure the formgrader to authenticate users through JupyterHub so that only specified graders may access the formgrader. See :doc:`<11_jupyerhub_config>` for more details.
