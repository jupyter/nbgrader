---
title: 'nbgrader: A Tool for Creating and Grading Assignments in the Jupyter Notebook'
tags:
- jupyter
- jupyterhub
- grading
- autograding
authors:
- name: Project Jupyter
- name: David Bourgin
  orcid: 0000-0003-1039-6195
  affiliation: 1
- name: Matthias Bussonnier
  orcid: 
  affiliation: 1
- name: Jonathan Frederic
  orcid: 0000-0003-4805-2216
  affiliation: 2
- name: Brian Granger
  orcid: 
  affiliation: 3
- name: Jessica Hamrick
  orcid: 0000-0002-3860-0429
  affiliation: 4
- name: Logan Page
  orcid: 0000-0002-5799-8524
  affiliation: 5
- name: Fernando Pérez
  orcid: 
  affiliation: 1
- name: Benjamin Ragan-Kelley
  orcid: 0000-0002-1023-7082
  affiliation: 6
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
date: 2 June 2018
bibliography: paper.bib
---

*Note: Authors on this paper are listed in alphabetical order.*

# Summary

nbgrader is a tool for creating and grading assignments in the Jupyter notebook [@kluyver2016jupyter]. nbgrader allows instructors to create a single, master copy of the assignment, from which the student version is generated—thus obviating the need to maintain two separate versions. nbgrader automatically grades submitted assignments by executing the notebooks and storing the results in a database. After auto-grading, instructors can provide partial credit or manually grade free-responses using the *formgrader* notebook extension. Finally, instructors can use nbgrader to leave personalized feedback for each student, including instructor comments as well as detailed error information.

When used with JupyterHub [@JupyterHub], nbgrader provides additional workflow functionality that covers the entire grading process. After creating the assignment, instructors can release it to students, who can then fetch a copy of the assignment directly through the notebook server interface. Students can submit their completed version through the same interface, making it available for instructors to collect with one command. After that, instructors can use the auto-grading functionality as normal and may access the formgrader as a JupyterHub service.

Since its conception in September 2014, nbgrader has been "battle-tested" in a number of classes all over the world, including at UC Berkeley, Cal Poly San Luis Obispo, University of Pretoria, University of Edinburgh, Northeastern University, Central Connecticut State University, KTH Royal Institute of Technology Stockholm, CU Boulder, University of Amsterdam, George Washington University, Texas A&M University, Bryn Mawr College, and University of Maryland; and, as of May 2018, over 10,000 nbgrader-based notebooks exist on GitHub. In addition to its core functionality, nbgrader has expanded to support a number of features, including the ability to handle multiple classes on the same JupyterHub instance; the option to either include or hide autograder tests; customizable late penalties; and support for importing assignment files downloaded from a LMS (Learning Management System). As we continue to develop nbgrader, we always keep it’s original aim in mind: to provide a flexible, straightforward system for creating and grading assignments in the Jupyter notebook.

# Statement of Need

The use of computational methods has become increasingly widespread in fields outside of computer science. As these disciplines require more computational tools, undergraduate curricula also begin to include topics in programming and computer science. However, because students are focused on their own discipline—and programming is likely a secondary interest—teaching students through traditional computer science offerings is not always effective [@Cortina2007; @Forte2005; @Guzdial2005]. While there are visual programming languages such as Raptor [@Carlisle2004] or Scratch [@Resnick2009] that are intended to be easy and enjoyable for non-computer science majors to learn, they lack the specialized tools that are required for effective work in domain sciences, such as numerical or data visualization libraries. A hybrid approach is to teach students computational concepts in an interactive environment where it is possible to quickly write, test, and tweak small pieces of code. Many such environments exist, including Mathematica [@mathematica], Maple [@maple], Matlab [@matlab], Sage [@sage] and IPython [@PerezGranger2007].

In recent years the IPython project introduced the *Jupyter notebook* [@kluyver2016jupyter], an interface that is particularly conducive to interactive and literate computing where programmers can interleave prose with code and figures. The Jupyter notebook is ideal for educators because it allows them to create assignments which include instructions along with cells, in which students can provide solutions to exercises. Students can, for example, be asked to write code both to compute and visualize a particular result. Because of the interactive nature of the notebook, students can iterate on a coding problem without having to switch back and forth between the command line and a text editor, and they can see the results of their code almost instantly.

Instructors in many fields have already begun using the Jupyter notebook as a teaching platform. The notebook has appeared in over 70 classes [@Castano_Jupyter_Map_Dataset] on subjects including geology, mathematics, mechanical engineering, data science, chemical engineering, and bioinformatics, just to name a few. Software Carpentry, which aims to teach graduate students basic computational skills, has also adopted the notebook for some of its lessons [@Wilson2014].

Despite its appearance in many classrooms—prior to the existence of nbgrader—the notebook was rarely used on a large scale for *graded* assignments. Instead, it was often used either for ungraded in-class exercises; or in classes small enough that notebooks can be graded by hand. This is because there are several challenges to using the notebook for graded assignments at scale. First, for large class sizes, it is not feasible for an instructor to manually grade the code that students write: there must be a way of autograding the assignments. A Jupyter notebook is not a typical script that can be run and may contain multiple parts of a problem within the same notebook. Second, for many courses, the programming is a means to an end for understanding concepts in a specific domain. Instructors may also want students to provide written free-responses interpreting the results of their code, and thus need to be able to rely on autograding for the coding parts of an assignment, but also be able to manually grade the written responses in the surrounding context of the student's code. Third, the process of distributing assignments to students and later collecting them can be tedious, and this is true even more so with Jupyter notebooks because there is a separate interface for accessing them beyond the standard system file browser. This often leads to confusion on the part of students about how to open notebooks after downloading them, and where to find the notebooks in order to submit them.

nbgrader streamlines the repetitive tasks found in course management and grading, and its flexibility allows greater communication between instructor and student. Overall, nbgrader improves the learning experience as students and instructors can focus on content and building understanding by minimizing or automating the tedious and repetitive tasks.

# References

* nbgrader source code: [https://github.com/jupyter/nbgrader](https://github.com/jupyter/nbgrader)
* nbgrader documentation: [http://nbgrader.readthedocs.io/en/stable/](http://nbgrader.readthedocs.io/en/stable/)
