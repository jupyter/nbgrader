Using nbgrader with JupyterHub
==============================

.. seealso::

    :doc:`/user_guide/creating_and_grading_assignments`
        Documentation for ``nbgrader assign``, ``nbgrader autograde``, ``nbgrader formgrade``, and ``nbgrader feedback``.

    :doc:`/user_guide/managing_assignment_files`
        Documentation for ``nbgrader release``, ``nbgrader fetch``, ``nbgrader submit``, and ``nbgrader collect``.

    :doc:`/command_line_tools/nbgrader-formgrade`
        Command line options for ``nbgrader formgrade``

    :doc:`config_options`
        Details on ``nbgrader_config.py``

    :doc:`/user_guide/philosophy`
        More details on how the nbgrader hierarchy is structured.

    `JupyterHub Documentation <https://jupyterhub.readthedocs.io/en/latest/getting-started.html>`_
        Detailed documentation describing how JupyterHub works, which is very
        much required reading if you want to integrate the formgrader with
        JupyterHub.

For instructors running a class with JupyterHub, nbgrader offers several tools
that optimize and enrich the instructors' and students' experience of sharing
the same system. By integrating with JupyterHub, nbgrader streamlines the
process of releasing and collecting assignments for the instructor and of
fetching and submitting assignments for the student. In addition to using the
``nbgrader release``, ``nbgrader fetch``, ``nbgrader submit``, and ``nbgrader
collect`` commands (see :doc:`/user_guide/managing_assignment_files`) with a
shared server setup like JupyterHub, the formgrader (see
:doc:`/user_guide/creating_and_grading_assignments`) can be configured to integrate with
JupyterHub so that all grading can occur on the same server.

To set up the formgrader to work with JupyterHub, you will need to specify a
few custom config options (see :doc:`config_options` for details on all
possible config options, and where configuration files live). In this
documentation, we'll go through an example setup of JupyterHub with nbgrader,
though note that each deployment of JupyterHub is slightly different, which
might also require a slightly different nbgrader configuration. If you run into
problems getting nbgrader to work with JupyterHub, please do `open an issue
<https://github.com/jupyter/nbgrader/issues/new>`_!

.. warning::

    The way that the formgrader integrates with JupyterHub changed between
    versions 0.3 and 0.4 in a backwards-incompatible way. However, this means
    that the formgrader should be now much, much easier to use with JupyterHub
    than it was before!

Configuring JupyterHub
~~~~~~~~~~~~~~~~~~~~~~

To begin, we'll run a vanilla JupyterHub with the following
``jupyterhub_config.py``:

.. literalinclude:: jupyterhub/jupyterhub_config.py
   :language: python

The way we have set up the formgrader is as a `managed JupyterHub service
<http://jupyterhub.readthedocs.io/en/latest/services.html>`__. This means that
JupyterHub will keep track of the formgrader process for us, including
automatically routing requests from
``localhost:8000/services/formgrader-course101`` to the formgrader at
``localhost:9000``, and configuring the formgrader to only allow access from
usernames specified in the list of graders.

Configuring nbgrader formgrade
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make the formgrader integrate with JupyterHub, we must tell it to
authenticate users with JupyterHub. The following is an example
``nbgrader_config.py`` that does this:

.. literalinclude:: jupyterhub/nbgrader_config.py
   :language: python

In this example, the formgrader listens on localhost at port 9000, and uses the
special ``HubAuth`` authenticator class which knows how to talk to JupyterHub.

Configuring SSL
~~~~~~~~~~~~~~~

.. warning::

    As of nbgrader version 0.4.0, there is no longer any additional
    configuration that needs to be done to run with JupyterHub SSL support.

For a minimal working example of using JupyterHub with SSL, please see the
``nbgrader.tests.formgrader.manager.HubAuthSSLManager`` in the `nbgrader tests
<https://github.com/jupyter/nbgrader/blob/master/nbgrader/tests/formgrader/manager.py>`__.

Running JupyterHub and formgrader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The way we have set up the formgrader is as a `managed JupyterHub service
<http://jupyterhub.readthedocs.io/en/latest/services.html>`__. This means that
JupyterHub will keep track of the formgrader process for us. So, to run both
the formgrader and JupyterHub, we only need to actually run JupyterHub:

.. code:: bash

    jupyterhub

Running this command should launch JupyterHub, which will then be accessible
from ``localhost:8000``. It will also launch the formgrader, which you should
be able to access from ``localhost:8000/services/formgrader-course101``. If you
properly configured the ``notebook_url_prefix``, you should additionally be
able to open live notebooks from the formgrader using your notebook server that
was spawned by JupyterHub.
