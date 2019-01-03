---
title: 'nbgrader: A Tool for Creating and Grading Assignments in the Jupyter Notebook'
tags:
- jupyter
- jupyterhub
- grading
- autograding
authors:
- name: Project Jupyter
- name: Douglas Blank
  orcid: 0000-0003-3538-8829
  affiliation: 7
- name: David Bourgin
  orcid: 0000-0003-1039-6195
  affiliation: 1
- name: Alexander Brown
  orcid: 0000-0002-3945-7337
  affiliation: 8
- name: Matthias Bussonnier
  orcid: 0000-0002-7636-8632
  affiliation: 1
- name: Jonathan Frederic
  orcid: 0000-0003-4805-2216
  affiliation: 2
- name: Brian Granger
  orcid: 0000-0002-5223-6168
  affiliation: 3
- name: Thomas L. Griffiths
  orcid: 0000-0002-5138-7255
  affiliation: 1
- name: Jessica Hamrick
  orcid: 0000-0002-3860-0429
  affiliation: 4
- name: Kyle Kelley
  orcid: 0000-0002-4281-9351
  affiliation: 9
- name: M Pacer
  orcid: 0000-0002-6680-2941
  affiliation: 9
- name: Logan Page
  orcid: 0000-0002-5799-8524
  affiliation: 5
- name: Fernando Pérez
  orcid: 0000-0002-1725-9815
  affiliation: 1
- name: Benjamin Ragan-Kelley
  orcid: 0000-0002-1023-7082
  affiliation: 6
- name: Jordan W. Suchow
  orcid: 0000-0001-9848-4872
  affiliation: 1
- name: Carol Willing
  orcid: 0000-0002-9817-8485
  affiliation: 3
affiliations:
- name: University of California, Berkeley
  index: 1
- name: Google Inc.
  index: 2
- name: Cal Poly, San Luis Obispo
  index: 3
- name: DeepMind
  index: 4
- name: University of Pretoria
  index: 5
- name: Simula Research Laboratory
  index: 6
- name: Bryn Mawr College
  index: 7
- name: Lafayette College
  index: 8
- name: Netflix, Inc.
  index: 9
date: 2 June 2018
bibliography: paper.bib
---

*Note: Authors on this paper are listed in alphabetical order.*

# Summary

nbgrader is a flexible tool for creating and grading assignments in the Jupyter
Notebook [@kluyver2016jupyter]. nbgrader allows instructors to create a single,
master copy of an assignment, including tests and canonical solutions. From the
master copy, a student version is generated without the solutions, thus
obviating the need to maintain two separate versions. nbgrader also
automatically grades submitted assignments by executing the notebooks and
storing the results of the tests in a database. After auto-grading, instructors
can manually grade free responses and provide partial credit using the
*formgrader* Jupyter Notebook extension. Finally, instructors can use nbgrader
to leave personalized feedback for each student's submission, including comments
as well as detailed error information.

nbgrader can also be used with JupyterHub [@JupyterHub], which is a centralized,
server-based installation that manages user logins and management of Jupyter
Notebook servers. When used with JupyterHub, nbgrader provides additional
workflow functionality, covering the entire grading process. After creating an
assignment, instructors can distribute it to students, who can then fetch a copy
of the assignment directly through the Jupyter Notebook server interface.
Students can submit their completed assignment through the same interface,
making it available for instructors. After students submit their assignments,
instructors can collect the assignments with a single command and use the
auto-grading functionality in the normal way.

Since its conception in September 2014, nbgrader has been used in a number of
educational contexts, including courses at UC Berkeley, Cal Poly, University of
Pretoria, University of Edinburgh, Northeastern University, Central Connecticut
State University, KTH Royal Institute of Technology, CU Boulder, University of
Amsterdam, George Washington University, Texas A&M, Bryn Mawr College, Lafayette
College, and University of Maryland; and, as of May 2018, over 10,000
nbgrader-based notebooks exist on GitHub. In addition to its core functionality,
nbgrader has expanded to support a number of other features, including the
ability to handle multiple courses on the same JupyterHub instance; the option
to either include or hide automatically graded tests; customizable late
penalties; and support for importing assignment files downloaded from a Learning
Management System (LMS).

# Statement of Need

The use of computational methods has become increasingly widespread in fields
outside of computer science [@wing2008computational]. As these disciplines begin
to require computational tools, undergraduate curricula also begin to include
topics in programming and computer science. However, perhaps because students
are focused on the discipline that is the object of their study—and programming
is likely a secondary interest—it has been shown that teaching computer science
can be more effective when courses include interdisciplinary motivations
[@Cortina2007; @Forte2005; @Guzdial2005]. One approach for teaching programming
in a way that facilitates exploration with interdisciplinary questions is to
teach students computational concepts in an interactive environment where it is
possible to quickly write, test, and tweak small units of code. Many such
environments exist, including Mathematica [@mathematica], Maple [@maple], MATLAB
[@matlab], Sage [@sage] and IPython [@PerezGranger2007]. However, these are
often focused on programming in a single language, and lack an efficient system
for distributing, collecting, and evaluating student work.

In recent years, the IPython project introduced the *Jupyter Notebook*
[@kluyver2016jupyter], an interface that is conducive to interactive and
literate computing, where programmers can interleave prose with code, equations,
figures, and other media. The Jupyter Notebook was originally developed for
programming in the Python programming language, but multiple languages are now
supported using the same infrastructure. The Jupyter Notebook is ideal for
educators because it allows them to create assignments which include
instructions along with code or Markdown cells, in which students can provide
solutions to exercises. Students can, for example, write code both to compute
and visualize a particular result. Because the Jupyter Notebook is interactive,
students can iterate on a coding problem without needing to switch back and
forth between a command line and a text editor, and they can rapidly see results
alongside the code which produced them.

Instructors in many fields have begun using the Jupyter Notebook as a teaching
platform. The Jupyter Notebook has appeared in over 100 classes [@Hamrick2016;
@Castano_Jupyter_Map; @Castano_Jupyter_Map_Dataset] on subjects including
geology, mathematics, mechanical engineering, data science, chemical
engineering, and bioinformatics. Software Carpentry, an organization that aims
to teach graduate students basic computational skills, has also adopted the
Jupyter Notebook for some of its lessons [@Wilson2014].

Despite its appearance in many classrooms, yet before the existence of nbgrader,
the Jupyter Notebook was rarely used on a large scale for *graded* assignments.
Instead, it was often used either for ungraded in-class exercises, or in classes
small enough that notebooks could be graded by hand (sometimes even by printing
them out on paper and grading them like a traditional assignment). This is
because there are several challenges to using the Jupyter Notebook for graded
assignments at scale. First, for large classes, it is not feasible for an
instructor to manually grade the code that students write: there must be a way
to automatically grade the assignments. However, a notebook is not a typical
script that can be run and may contain multiple parts of a problem within the
same notebook; thus, automatically grading a notebook is less straightforward
than it is for a traditional script. Second, for many courses, programming is a
means to an end: understanding concepts in a specific domain. Specifically,
instructors may want students to provide both code and written free-responses
interpreting the results of that code. Instructors thus need to be able to rely
on automatic grading for the coding parts of an assignment, but also be able to
manually grade the written responses in the surrounding context of the student's
code. Third, the process of distributing assignments to students and later
collecting them can be tedious, even more so with the Jupyter Notebook because
there is a separate interface for accessing notebooks beyond the standard system
file browser. This often leads to confusion on the part of students about how to
open notebooks after downloading them, and where to find the notebooks in order
to submit them.

nbgrader streamlines the repetitive tasks found in course management and
grading, and its flexibility allows greater communication between instructor and
student. nbgrader has moreover enabled instructors to use Jupyter Notebook-based
assignments in classes with hundreds of students, which was previously not
possible to do without excessive human effort. Overall, nbgrader does—and with
further development will continue to—improve the learning experience for both
instructors and students, enabling them to focus on content and building
understanding.


# References

* nbgrader source code: [https://github.com/jupyter/nbgrader](https://github.com/jupyter/nbgrader)
* nbgrader documentation: [http://nbgrader.readthedocs.io/en/stable/](http://nbgrader.readthedocs.io/en/stable/)
