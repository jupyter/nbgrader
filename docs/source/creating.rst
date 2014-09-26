Creating an assignment
======================

**These instructions are currently incomplete**.

Creating an assignment consists of creating a student version of a notebook that
has solutions omited.

1. Create a notebook that has exercises, solutions and tests.
2. Tag the solution and test cells.
3. Generate the student version of the assignment::

       nbgrader assign --output=StudentNotebook.ipynb TeacherNotebook.ipynb

4. Distribute the student version of the notebook to the students and
   have them use it in doing their work.
