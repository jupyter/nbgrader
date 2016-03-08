Interface highlights
====================

Instructor toolbar extension for Jupyter notebooks
--------------------------------------------------
The nbgrader toolbar extension for Jupyter notebooks guides the instructor through
assignment and grading tasks using the familiar Jupyter notebook interface.
For example, creating an assignment has the following workflow:

.. image:: images/creating_assignment.gif
   :alt: Creating assignment

Student assignment list extension for Jupyter notebooks
-------------------------------------------------------
Using the assignment list extension, students may conveniently view, fetch,
submit, and validate their assignments:

.. image:: images/student_assignment.gif
   :alt: nbgrader assignment list

The command line tools of nbgrader
----------------------------------
Command line tools offer an efficient way for the instructor to generate,
assign, release, collect, and grade notebooks. Here are some of the commands:

* `nbgrader assign`: create a student version of a notebook
* `nbgrader release`: release a notebook to students
* `nbgrader collect`: collect students' submissions
* `nbgrader autograde`: autograde students' submissions
* `nbgrader formgrade`: launch the formgrader

Try it out!
-----------

You can try out nbgrader for yourself without installing anything on your system by `running the demo <https://github.com/jhamrick/nbgrader-demo>`_. This demo is provided through `Binder <http://www.mybinder.org/>`_ and runs entirely in your browser without you needing to install anything. It goes through all the different nbgrader steps that are documented in this User Guide, from creating assignments, to distributing them, to grading them.
