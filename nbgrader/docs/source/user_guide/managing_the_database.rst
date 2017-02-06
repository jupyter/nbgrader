
Managing the database
=====================

.. seealso::

    :doc:`/command_line_tools/nbgrader-db-student-add`
        Command line options for ``nbgrader db student add``

    :doc:`/command_line_tools/nbgrader-db-student-import`
        Command line options for ``nbgrader db student import``

    :doc:`/command_line_tools/nbgrader-db-student-remove`
        Command line options for ``nbgrader db student remove``

    :doc:`/command_line_tools/nbgrader-db-student-list`
        Command line options for ``nbgrader db student list``

    :doc:`/command_line_tools/nbgrader-db-assignment-add`
        Command line options for ``nbgrader db assignment add``

    :doc:`/command_line_tools/nbgrader-db-assignment-import`
        Command line options for ``nbgrader db assignment import``

    :doc:`/command_line_tools/nbgrader-db-assignment-remove`
        Command line options for ``nbgrader db assignment remove``

    :doc:`/command_line_tools/nbgrader-db-assignment-list`
        Command line options for ``nbgrader db assignment list``

    :doc:`philosophy`
        More details on how the nbgrader hierarchy is structured.

    :doc:`/configuration/config_options`
        Details on ``nbgrader_config.py``

Most of the important information that nbgrader has access
to---information about students, assignments, grades, etc.---is stored
in the nbgrader database. Much of this is added to the database
automatically by nbgrader, with the exception of two types of
information: which students are in your class, and which assignments you
have.

There are three methods for adding students and assignments to the
database. The first is by declaring them explicitly in the
``nbgrader_config.py`` file, such as:

.. code:: python

    c = get_config()
    c.NbGrader.db_assignments = [dict(name="ps1", duedate="2015-02-02 17:00:00 UTC")]
    c.NbGrader.db_students = [
        dict(id="bitdiddle", first_name="Ben", last_name="Bitdiddle"),
        dict(id="hacker", first_name="Alyssa", last_name="Hacker")
    ]

The second is by writing a Python script and using the :doc:`API </api/index>`. The third way is to use the command line tool ``nbgrader db``, which provides limited command line access to some of the API functionality.

.. code:: 

    %%bash
    
    # remove the existing database, to start fresh
    rm gradebook.db

Managing assignments
--------------------

To add assignments, we can use the ``nbgrader db assignment add``
command, which takes the name of the assignment as well as optional
arguments (such as its due date):

.. code:: 

    %%bash
    
    nbgrader db assignment add ps1 --duedate="2015-02-02 17:00:00 UTC"


.. parsed-literal::

    [DbAssignmentAddApp | INFO] Creating/updating assignment with ID 'ps1': {'duedate': '2015-02-02 17:00:00 UTC'}


After we have added the assignment, we can view what assignments exist
in the database with ``nbgrader db assignment list``:

.. code:: 

    %%bash
    
    nbgrader db assignment list


.. parsed-literal::

    There are 1 assignments in the database:
    ps1 (due: 2015-02-02 17:00:00)


An alternate way to add assignments is a batch method of importing a CSV
file. The file must have a column called ``name``, and may optionally
have columns for other assignment properties (such as the due date):

.. code:: 

    %%file assignments.csv
    name,duedate
    ps1,2015-02-02 17:00:00 UTC
    ps2,2015-02-09 17:00:00 UTC


.. parsed-literal::

    Writing assignments.csv


Then, to import this file, we use the ``nbgrader db assignment import``
command:

.. code:: 

    %%bash
    
    nbgrader db assignment import assignments.csv


.. parsed-literal::

    [DbAssignmentImportApp | INFO] Importing assignments from: 'assignments.csv'
    [DbAssignmentImportApp | INFO] Creating/updating assignment with name 'ps1': {'duedate': '2015-02-02 17:00:00 UTC'}
    [DbAssignmentImportApp | INFO] Creating/updating assignment with name 'ps2': {'duedate': '2015-02-09 17:00:00 UTC'}


We can also remove assignments from the database with
``nbgrader db assignment remove``. **Be very careful using this command,
as it is possible you could lose data!**

.. code:: 

    %%bash
    
    nbgrader db assignment remove ps1


.. parsed-literal::

    [DbAssignmentRemoveApp | INFO] Removing assignment with ID 'ps1'


Managing students
-----------------

Managing students in the database works almost exactly the same as
managing assignments. To add students, we use the
``nbgrader db student add`` command:

.. code:: 

    %%bash
    
    nbgrader db student add bitdiddle --last-name=Bitdiddle --first-name=Ben
    nbgrader db student add hacker --last-name=Hacker --first-name=Alyssa


.. parsed-literal::

    [DbStudentAddApp | INFO] Creating/updating student with ID 'bitdiddle': {'last_name': 'Bitdiddle', 'email': None, 'first_name': 'Ben'}
    [DbStudentAddApp | INFO] Creating/updating student with ID 'hacker': {'first_name': 'Alyssa', 'last_name': 'Hacker', 'email': None}


And to list the students in the database, we use the
``nbgrader db student list`` command:

.. code:: 

    %%bash
    
    nbgrader db student list


.. parsed-literal::

    There are 2 students in the database:
    bitdiddle (Bitdiddle, Ben) -- None
    hacker (Hacker, Alyssa) -- None


Like with the assignments, we can also batch add students to the
database using the ``nbgrader db student import`` command. We first have
to create a CSV file, which is required to have a column for ``id``, and
optionally may have columns for other student information (such as their
name):

.. code:: 

    %%file students.csv
    id,last_name,first_name,email
    bitdiddle,Bitdiddle,Ben,
    hacker,Hacker,Alyssa,


.. parsed-literal::

    Writing students.csv


.. code:: 

    %%bash
    
    nbgrader db student import students.csv


.. parsed-literal::

    [DbStudentImportApp | INFO] Importing students from: 'students.csv'
    [DbStudentImportApp | INFO] Creating/updating student with ID 'bitdiddle': {'last_name': 'Bitdiddle', 'email': None, 'first_name': 'Ben'}
    [DbStudentImportApp | INFO] Creating/updating student with ID 'hacker': {'last_name': 'Hacker', 'email': None, 'first_name': 'Alyssa'}


We can also remove students from the database with
``nbgrader db student remove``. **Be very careful using this command, as
it is possible you could lose data!**

.. code:: 

    %%bash
    
    nbgrader db student remove bitdiddle


.. parsed-literal::

    [DbStudentRemoveApp | INFO] Removing student with ID 'bitdiddle'

