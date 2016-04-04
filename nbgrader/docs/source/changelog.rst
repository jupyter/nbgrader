Changelog
=========

A summary of changes to nbgrader.

0.2.x
-----

0.2.2
~~~~~

Adds some improvements to the documentation and fixes a few small bugs:

- Add requests as a dependency
- Fix a bug where the "Create Assignment" extension was not rendering correctly in Safari
- Fix a bug in the "Assignment List" extension when assignment names had periods in them
- Fix integration with JupyterHub when SSL is enabled
- Fix a bug with computing checksums of cells that contain UTF-8 characters under Python 2

0.2.1
~~~~~

Fixes a few small bugs in v0.2.0:

- Make sure checksums can be computed from cells containing unicode characters
- Fixes a bug where nbgrader autograde would crash if there were any cells with blank grade ids that weren't actually marked as nbgrader cells (e.g. weren't tests or read-only or answers)
- Fix a few bugs that prevented postgres from being used as the database for nbgrader

0.2.0
~~~~~

Version 0.2.0 of nbgrader primarily adds support for version 4.0 of the Jupyter notebook and associated project after The Big Split. The full list of major changes are:

- Jupyter notebook 4.0 support
- Make it possible to run the formgrader inside a Docker container
- Make course_id a requirement in the transfer apps (list, release, fetch, submit, collect)
- Add a new assignment list extension which allows students to list, fetch, validate, and submit assignments from the notebook dashboard interface
- Auto-resize text boxes when giving feedback in the formgrader
- Deprecate the BasicConfig and NbGraderConfig classes in favor of a NbGrader class

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.2.0 release:

- alope107
- Carreau
- ellisonbg
- jhamrick
- svurens

0.1.0
-----

I'm happy to announce that the first version of nbgrader has (finally) been released! nbgrader is a tool that I've been working on for a little over a year now which provides a suite of tools for creating, releasing, and grading assignments in the Jupyter notebook. So far, nbgrader has been used to grade assignments for the class I ran in the spring, as well as two classes that Brian Granger has taught.

If you have any questions, comments, suggestions, etc., please do open an issue on the bugtracker. This is still a very new tool, so I am sure there is a lot that can be improved upon!

Thanks so much to all of the people who have contributed to this release by reporting issues and/or submitting PRs:

- alope107
- Carreau
- ellachao
- ellisonbg
- ivanslapnicar
- jdfreder
- jhamrick
- jonathanmorgan
- lphk92
- redSlug
- smeylan
- suchow
- svurens
- tasilb
- willingc
