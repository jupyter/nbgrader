.. nbgrader documentation master file, created by
   sphinx-quickstart on Fri Sep 26 13:20:30 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation for nbgrader
==========================

* :ref:`guide`
* :ref:`cmdline`
* :ref:`api`

.. _guide:

User guide
----------

.. toctree::
   :maxdepth: 1

   guide/install
   guide/developing
   guide/releasing
   guide/autograding
   guide/formgrading

.. _cmdline:

Command line programs
---------------------

``nbgrader`` includes three subcommands:

.. toctree::
   :hidden:
   :glob:

   apps/*

* :ref:`assign`: create the release version of an assignment to give to students
* :ref:`autograde`: autograde a student's submitted assignment
* :ref:`formgrade`: grade a student's submitted assignment with a Google Form

.. _api:

Source documentation
--------------------

.. toctree::
   :maxdepth: 2
   :glob:

   api/*
