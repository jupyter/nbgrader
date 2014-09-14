# nbgrader

A system for assigning and grading notebooks.

**These instructions are currently incomplete**.

## Create an asssignment

Creating an assignment consists of creating a student version of a notebook that
has solutions omited.

1. Create a notebook that has exercises, solutions and tests.
2. Tag the solution and test cells.
3. Generate the student version of the assignment.

```
nbgrader assign --output=StudentNotebook.ipynb TeacherNotebook.ipynb
```

4. Distribute the student version of the notebook to the students and
   have them use it in doing their work.

## Autograde a students solution

Let's say that students have turned in their notebooks with a special naming convention
of `StudentNotebookLastname.ipynb`. If all of the student notebooks are in the current
directory, autograde all of them by doing:

```
nbgrader autograde StudentNotebook*.ipynb
```

## Grade a students solution using an embedded Google Form

```
nbgrader formgrade StudentNotebook*.ipynb
```