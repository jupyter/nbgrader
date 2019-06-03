Advanced topics
===============

This file covers some more advanced use cases of nbgrader.

.. contents:: Table of contents
   :depth: 2

Running nbgrader with JupyterHub
--------------------------------

Please see :doc:`/configuration/jupyterhub_config`.

.. _assignment-list-installation:

Advanced "Assignment List" installation
---------------------------------------

.. seealso::

  :doc:`installation`
    General installation instructions.

  :doc:`managing_assignment_files`
    Details on fetching and submitting assignments using the "Assignment List"
	plugin.

.. warning::

  The "Assignment List" extension is not currently compatible with multiple
  courses on the same server: it will only work if there is a single course on
  the server. This is a known issue (see `#544
  <https://github.com/jupyter/nbgrader/issues/544>`__). :ref:`PRs welcome!
  <pull-request>`

This section covers some further and configuration scenarios that often
occur with the *assignment list* extension.

In previous versions of nbgrader, a special process had to be used to enable
this extension for all users on a multi-user system. As described in the main
:doc:`installation` documentation this is no longer required.

If you know you have released an assignment but still don't see it in the list
of assignments, check the output of the notebook server to see if there are any
errors. If you do in fact see an error, try running the command manually on the
command line from the directory where the notebook server is running. For
example:

.. code:: bash

  $ nbgrader list
  [ListApp | ERROR] Unwritable directory, please contact your instructor: /srv/nbgrader/exchange

This error that the exchange directory isn't writable is an easy mistake to
make, but also relatively easy to fix. If the exchange directory is at
``/srv/nbgrader/exchange``, then make sure you have run:

.. code:: bash

  chmod +rw /srv/nbgrader/exchange

.. _getting-information-from-db:

Getting information from the database
-------------------------------------

nbgrader offers a fairly rich :doc:`API </api/index>` for interfacing with the
database. The API should allow you to access pretty much anything you want,
though if you find something that can't be accessed through the API please
`open an issue <https://github.com/jupyter/nbgrader/issues/new>`_!

In this example, we'll go through how to create a CSV file of grades for each
student and assignment using nbgrader and `pandas
<http://pandas.pydata.org/>`__.

.. versionadded:: 0.4.0
    nbgrader now comes with CSV export functionality out-of-the box using the
    :doc:`nbgrader export </command_line_tools/nbgrader-export>` command.
    However, this example is still kept for reference as it may be useful for
    :doc:`defining your own exporter </plugins/export-plugin>`.

.. literalinclude:: extract_grades.py
   :language: python

After running the above code, you should see that ``grades.csv`` contains something that looks like::

    student,assignment,max_score,score
    bitdiddle,ps1,9.0,1.5
    hacker,ps1,9.0,3.0

Using nbgrader preprocessors
----------------------------

Several of the nbgrader preprocessors can be used with nbconvert without
actually relying on the rest of the nbgrader machinery. In particular, the
following preprocessors can be applied to other nbconvert workflows:

- ``ClearOutput`` -- clears outputs of all cells
- ``ClearSolutions`` -- removes solutions between the
  solution delimeters (see :ref:`autograded-answer-cells`).
- ``HeaderFooter`` -- concatenates notebooks together,
  prepending a "header" notebook and/or appending a "footer" notebook to
  another notebook.
- ``LimitOutput`` -- limits the amount of output any given
  cell can have. If a cell has too many lines of outputs, they will be
  truncated.

Using these preprocessors in your own nbconvert workflow is relatively
straightforward. In your ``nbconvert_config.py`` file, you would add, for
example:

.. code:: python

    c.Exporter.preprocessors = ['nbgrader.preprocessors.ClearSolutions']

See also the nbconvert docs on `custom preprocessors <https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html#Custom-Preprocessors>`__.

Calling nbgrader apps from Python
---------------------------------

.. versionadded:: 0.5.0
    Much of nbgrader's high level functionality can now be accessed through
    an official :doc:`Python API </api/high_level_api>`.

.. _grading-in-docker:

Grading in a docker container
-----------------------------

For security reasons, it may be advantageous to do the grading with a kernel
running in isolation, e.g. in a docker container. We will assume that
docker is already installed and an appropriate image has been downloaded.
Otherwise, refer to the `docker documentation <https://docs.docker.com>`_
for information on how to install and run docker.

A convenient way to switch to a kernel running in a docker container is
provided by ``envkernel`` which serves a double purpose. In a first step,
it is writing a new kernelspec file. Later it ensures that the docker
container is run and the kernel started.

Presently, ``envkernel`` is only available from its `Github repository
<https://github.com/NordicHPC/envkernel>`_ and can be installed directly
from there into a virtual environment

.. code:: bash

    pip install https://github.com/NordicHPC/envkernel/archive/master.zip

As an alternative, the script ``envkernel.py`` can be put in a different
location, e.g. ``/opt/envkernel``, as long as it is accessible there also
later during grading.

Now, a new kernel can be installed by means of

.. code:: bash

    ./envkernel.py docker --name=NAME --display-name=DNAME DOCKER-IMAGE

Here, ``NAME`` should be replaced by the name to be given to the kernel.
After installation of the kernel, it will be displayed in the list of
kernels when executing ``jupyter kernelspec list``.  ``DNAME`` should be
replaced by the name under which the kernel shall be known in the Jupyter
notebook GUI. After installation of the kernel, this name will be listed as
a possible kernel when starting a new notebook. Finally, ``DOCKER-IMAGE``
should be replaced by the name of the docker image in which the kernel is
to be run, e.g. ``python:3``, ``continuumio/anaconda3``, or some other
suitable image.

The command given above will install the kernel in the system-wide location
for Jupyter data files. If installation in the corresponding user directory
is desired, the option ``--user`` should be added before the name of the
docker image. By default, ``envkernel`` will install a Python kernel. For
the installation of other kernels, see the `README
<https://github.com/NordicHPC/envkernel/blob/master/README.md>`_ of
``envkernel``.

In order to run the grading process with the new kernel, one can specify
its name in ``nbgrader_config.py``

.. code:: python

    c.ExecutePreprocessor.kernel_name = NAME

where ``NAME`` should be replaced by the name chosen when running the
``envkernel`` script. Alternatively, the name can be specified when running
nbgrader from the command line

.. code:: bash

    nbgrader autograde --ExecutePreprocessor.kernel_name=NAME ASSIGNMENT_NAME

In addition to docker, ``envkernel`` also supports singularity as a
containerization system. For details on using ``envkernel`` with
singularity, see the `README
<https://github.com/NordicHPC/envkernel/blob/master/README.md>`_ of
``envkernel``.
