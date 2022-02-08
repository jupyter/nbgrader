What is nbgrader?
=================

This page describes the internals of nbgrader from a rather technical
standpoint.  It is needed not just for developers, but also for
administrators which need to build advanced deployments, possibly
customizing various components in the process.

A companion (and minor prerequisite) to this is the `Jupyter
conceptual introduction
<https://jupyterhub.readthedocs.io/en/latest/getting-started/what-is-jupyterhub.html>`
(once it is released).



Working with nbgrader
---------------------

When nbgrader was first written, all interactions were done on the
command line. Later on it acquired notebook extensions to enable
interaction from within a jupyter notebook. These notes will refer to
the command-line interface, and we'll discuss the UI interactions
later.  Over time, this and other improvements have been added, but
because of the simple roots, it is not too difficult to dig deeper and
innovate to your specific case.



Nbgrader format
---------------

Nbgrader uses the **standard Jupyter notebook format**, ``.ipynb``.
This is the primary power of nbgrader: since it uses a standard format
that's used for other types of computation.  Since it is not special
to nbgrader, it is immediately usable on other systems (running on
your own computer, uploading to Google Colab, using anything from the
Jupyter ecosystem).  Thus, to begin developing nbgrader notebooks,
nothing special is needed.  They are directly portable to research
code, other projects, etc.  The skills learned in doing nbgrader
assignments is portable to other real-world projects.

All of the files are stored directly on a filesystem, so that they are
easy to manipulate and understand.  The text (well, JSON) based
notebook format is well supported by Jupyter tools for manipulation,
making it easy to script other tools with them.

`Jupyter notebooks can have metadata
<https://nbformat.readthedocs.io/en/latest/format_description.html>`__ -
both notebook-wide and per-cell.  This is used to track the progress
of the assignment.  For example, this tracks cells that are
read-only.  However, since the metadata is within the notebook file
itself - which is given to the student - one can't prevent the
student from editing the notebook file to change anything within it,
since they have direct access to the file within their server.
More on the effects of this later.

The standard Jupyter stack and notebook format is also one of the
downsides, compared to other learning management systems (depending on
if you consider this a disadvantage...).  Because this is not a
"captive system" that segments users from the data they are working
on, you can't easily limit access to the underlying operating system
or notebook file.  For example, it is very difficult to prevent access
to the actual ``.ipynb`` source file, if you wanted to do that.  The
student *actually* has access to the computational environment
(subject to the limits of the JupyterHub/spawner you set up, which
*can* limit students to their own environment).  However, if you
design your course considering this, we hope you'll see that this is
an advantage.



Course directory
----------------

From the instructor side, all data is stored in files in the **course
directory**.  Within this directory, files have the general structure
``{nbgrader_step}/{student_id}/{assignment_id}/{notebook}.ipynb``.
The ``{nbgrader_step}`` indicates the progress of the notebook:

* ``source/`` contains the raw source notebooks made by the
  instructor.  You run ``nbgrader generate_assignment`` to produce
  the...
* ``release/`` directory.  This contains a version with the "hidden
  tests" removed and various cells marked read-only.  For both the
  ``source`` and ``release`` steps, the ``student_id`` part of the
  path is missing, since the notebooks are not personalized per
  student.
* The release version gets copied to the students, and copied back.
  This can be through the "exchange" (below), or some other technique.
* The ``submitted/`` step contains the students submitted versions.
  By running ``nbgrader autograde``, the files are autograded (see
  below) and copied to the...
* ``autograded`` directory.  Autograding is described below, but
  basically consists of executing the notebook and looking for failed
  cells.  ``autograded`` stores the executed notebook.  One can also
  use this for manual grading.  Running ``generate_feedback``, one gets...
* ``feedback``.  This stores a ``.html`` (not ``.ipynb``) file with
  the executed notebook, points, and comments from manual grading.
  This can be returned to the students.

But, there is a database in **gradebook.db** which stores students and
grades.  Less obviously, it stores the assignments and the contents of
hidden or immutable cells, such as the contents of the hidden tests
or read-only cells.  This is used to restore these cells when students
return them.

Most operations primarily look at the filesystem to see the current
state, so that it is easy to understand and manipulate the
internals.  In other words, just by manipulating the files on disk,
you can control all of the nbgrader steps.  The gradebook is a sort of
secondary source of information most of the time.


nbgrader generate_assignment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``generate_assignment`` converts the release notebook file from the
source.  Like all of these commands, it is implemented as converters
that implement various filters of the notebook source, in this case
reading from a path in ``source/`` and writing to a path in
``release/``.  Exact operations can be found within the
``nbgrader.converters`` path.

The main effect of ``generate_assignment`` is to strip all output
cells and remove ``### BEGIN SOLUTION`` AND ``### BEGIN HIDDEN TEST``
blocks, and record the contents of various read-only cells in the
database.



nbgrader autograde
~~~~~~~~~~~~~~~~~~

This is described below, but the core tasks are to re-insert the
read-only cells (replace them with the known-good versions), and
execute the entire notebook.  Note that there is a separate manual
grading step, but this isn't a nbgrader command, but done in the
formgrader interface.  This is described more below.



nbgrader generate_feedback
~~~~~~~~~~~~~~~~~~~~~~~~~~

This will take any feedback created during manual grading, for all
student submissions in this assignments, and create a .html file.
This uses the same machinery that `nbconvert
<https://nbconvert.readthedocs.io/>`__ uses, but with a custom
template that adds in information about grading, points, etc.



Collecting and releasing: collectors and the exchange
-----------------------------------------------------

There are various ways to release assignments to students and get them
back: something done out-of-nbgrader by you, using the filesystem
exchange, or (in the future) other exchanges.

Out-of-band exchange
~~~~~~~~~~~~~~~~~~~~

Originally, nbgrader had no built-in way of distributing assignments.
You would upload the assignments to your other course management
system, students would download, do it on their own computers (or
wherever - it's just a standard Jupyter notebook file, of course), and
upload to the course management system again.  The system hopefully
allows you to download the files of all students in bulk, organized in
a particular fashion (sorted by student username, for example).  You
can then use a nbgrader **collector** to import the tree of student
notebooks back into the ``submitted`` step of the course directory.

This is simple, effective, and relatively foolproof and secure - but
requires the student to create their own Jupyter environment to do the
assignment.  These days, Jupyter has the promise of the cloud, so
there is some way to manage this for the students:



Filesystem exchange
~~~~~~~~~~~~~~~~~~~

Let's say that you have a JupyterHub web server with accounts for all
students.  All students have access to the same system via JupyterHub,
properly segmented into user accounts.  The **filesystem exchange**
allows you to distribute the assignments, students to submit
completed assignments, and release feedback.  The filesystem exchange
is simple but effective.

It is structured as:

* ``outbound/``, containing assignments released to students.

  * Organized as ``outbound/{assignment_id}/{notebook}.ipynb``.  Other
    data files can be distributed along with the notebook.

  * Files are copied from ``{course_dir}/release/`` to
    ``{exchange_dir}/outbound/`` by the ``nbgrader release_assignment``
    command.

* ``inbound/``, containing assignments the student is submitting.  It
  should be writeable, but not listable, by students (``-wx`` UNIX
  permissions).

  * Organized as
    ``inbound/{studend_id}+{assignment_id}+{timestamp}+{random_string}/{notebook}.ipynb``.
    One of these directories contains one submission of the
    assignment.  The protection of them is within the random string,
    which is described below.

  * Files are copied from ``{exchange_dir}/inbound/`` to
    ``{course_dir}/submitted/`` by the ``nbgrader fetch_assignment``
    command.

* ``feedback/``, containing feedback to the students.  This should
  be traversable by students, but not listable (``--x``).  The
  files inside should be readable (``r--``).

  * Organized as ``feedback/{hash}.html``, where ``{hash}`` is a hash
    of notebook contents and timestamp of submission.  It serves as a
    key which is known to the student but not to other students, so
    that they can identify their notebook and retrieve it.

  * Files are copied from ``{course_dir}/feedback/`` to
    ``{exchange_dir}/feedback/`` by the ``nbgrader release_feedback``
    command.

The filesystem exchange relies on certain UNIX filesystem semantics:
if a user has write and execute permissions on a directory, they can
create files inside of it but not list other files in there.  If each
file has an unpredictable name (e.g. by a random string), students can
not access each others files (this is used for submitting
assignments).  Furthermore, they can access files they *do* know the
names of (this is used for retrieving feedback).  In order for these
assumptions to apply, students must access the  filesystem under
different numeric UNIX user ids (UIDs).

The filesystem exchange isn't limited to just one computer, though.
**Network filesystems** exist and have the necessary UNIX semantics - in
particular, the Network Filesystem (NFS).  This can easily be used to
mount an exchange directory on multiple computers, so that students
can be distributed among multiple computers within a cluster.
However, this requires a consistent mapping to UIDs across the
cluster.  This is not difficult to do, but if often not the way that
"cloud stuff" works by default.

The default filesystem exchange path is ``/srv/nbgrader/exchange``.
In a UNIX file system, this is by default owned by the root user, so
you will need to use a bit of knowledge to set things up properly.



Other exchanges
~~~~~~~~~~~~~~~

While a network-mounted filesystem exchange can work, it still is
limited to UNIX filesystem semantics, which is quite limited.  There
are API-based network exchanges under development, which will allow a
true decoupling of the student environment from the course management.

More generally, as part of that work, a **pluggable exchange** concept
is being developed, so that the exchange is a class which can be
replaced by custom implementations.



Student directories
-------------------

The basic principle is that the student copy of assignments are copied
to and from the student's home directory (on more precisely, the
working directory of the notebook server).  Once they are in the
student directory, they are accessed just like any other notebooks or
data the student can access.



Autograding
-----------

Autograding is very simple in principle: run the notebook.  The actual
effect is no different than the "Restart and run all cells"
functionality within the Jupyter interface.

The difference is that, after running, it looks for cells that have an
error output.  If any of these cells are marked as "autograder tests",
then these cells have a point value, and that point value is
subtracted.  Error output is simple any text on the `standard error
stream
<https://en.wikipedia.org/wiki/Standard_streams#Standard_error_(stderr)>`__,
which is saved separately within the notebook output from the standard
output stream.  It is up to the Jupyter kernel to write an error
message to the standard error stream, otherwise autograder doesn't
work (this has been a problem with a few languages kernels in the
past).

TODO: partial credit.  If a autograder test cell outputs a single
number to the standard output stream, then it will use that as the
number of points.  However, this could always be simulated by dividing
the autograded task into multiple cells.



Validation
~~~~~~~~~~

**Validation** is very related to autograding.  There is a button on
the student interface marked "validate", which executes the student
version of the notebook from top to bottom, and reports any errors.
This is exactly equivalent to "Restart and run all", but doesn't stop
on errors.  Since all it can access is the actual notebook file the
student has, it can not take into account the hidden tests.  If an
instructor wants a test to be visible to the students.

There is currently no support for inserting hidden tests into the
notebook file (perhaps you could in a hidden cell, but since the
student actually has the file... it's not going to be hidden to anyone
willing to do a bit of exploration).



Manual grading
--------------

After autograding, there is a web UI (via the formgrader extension) to
do **manual grading**.  This
allows one to see the output from autograding, give comments, adjust
points, etc.  There are also purely manually graded exercises.

The output from manual grading is only stored in ``gradebook.db``, and
is merged into the final output at the ``feedback`` step.



gradebook.db and student management
-----------------------------------

The **gradebook** or **database** is stored (by default) at
``gradebook.db`` at the root of the course directory.  Out of the box,
it is sqlite3, but can be other database systems, too.

First, the gradebook stores student mappings.  It stores a
``student_id`` (string) that is the name used on the filesystem for
each student.  It can also store a firstname/lastname/email for each
student, but it doesn't try to replace a complex student management
system.

The database also stores assignments and their cells.  For example, it
stores the contents of read-only cells, and autograder tests cells,
which get re-inserted into the notebook before the autograde step.
Cells are stored by the cell ID, which is in the cell metadata (cell
metadata is a ipynb-format native concept).
The autograder step looks at the database and re-inserts data based on
the cell ID.

In the formgrader "manual grading" interface, the instructor can
manually grade assignments (after autograding), and these points +
comments are added to the database.

Grades can be exported in csv format.  You can also build other
exporters, which access the database and export somehow - to a file,
or perhaps other fancy things like uploading directly.



Feedback
--------

Feedback is a HTML file, basically like a rendering of the notebook
using nbconvert.  However, it adds in points and feedback.

Historically, feedback was just generated, and it was up to the
teacher to distribute it somehow (for example, uploading to the course
management system or scripting copying it into users home
directories).  Now, using the exchange, there can be automatically
distributed.  This is described above.



Web extensions
--------------

Most of the above originally was handled via a command line
interface.  But now there are several interfaces directly from
Jupyter, and these are essentially the "default" ways of using
nbgrader.

The **Assignment list** extension serves as the student-facing
interface for the notebook file browser view.  It fetches assignments
from the exchange directory, allows students to open them, and submit
them back to the exchange.  This is for the Jupyter notebook
file-browser view

The **formgrader** extension is the instructor-facing interface
accessible from the file browser view.  It allows the instructor to
browse assignments, open them, manage students, etc.  This is for the
Jupyter notebook file-browser view.

The **validate** extension is a student-facing for the
notebook view that does validation.  Basically, it is the same as
"Restart and run all cells" but it shows errors a little bit nicer.

The **create assignment** extension is an instructor-facing for the
notebook view.  It provides a toolbar that allows you to edit cell
metadata.

Currently, these only work for the Jupyter notebook interface, not
JupyterLab.  This is a point under development.



See also
--------

* Noteable service, based on nbgrader

  * `Student guide <https://noteable.edina.ac.uk/student-guide/>`__
  * `Instructor guide <https://noteable.edina.ac.uk/documentation/nbguide/>`__
