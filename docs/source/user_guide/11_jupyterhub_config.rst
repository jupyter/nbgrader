Using nbgrader with JuptyerHub
==============================

.. seealso::

    :doc:`05_manual_grading`
        Documentation for ``nbgrader formgrade``.

    :doc:`/command_line_tools/nbgrader-formgrade`
        Command line options for ``nbgrader formgrade``

    :doc:`/config_options`
        Details on ``nbgrader_config.py``

    :doc:`01_philosophy`
        More details on how the nbgrader hierarchy is structured.

    `JupyterHub Documentation <https://github.com/jupyter/jupyterhub/blob/master/docs/getting-started.md>`_
        Detailed documentation describing how JupyterHub works, which is very
        much required reading if you want to integrate the formgrader with
        JupyterHub.

In addition to using the :doc:`nbgrader release <07_releasing_assignments>`,
:doc:`nbgrader fetch <08_fetching_assignments>`,
:doc:`nbgrader submit <09_submitting_assignments>`, and
:doc:`nbgrader collect <10_collecting_assignments>` commands with a shared
server setup like JupyterHub, the :doc:`formgrader <05_manual_grading>` can be
configured to integrate with JupyterHub so that all grading can occur on the
same server.

To set up the formgrader to work with JupyterHub, you will need to specify a
few custom config options (see :doc:`</config_options>` for details on all possible config options, and where configuration files live).
In this documentation, we'll go through an example
setup of JupyterHub with nbgrader, though note that each deployment of JupyterHub is slightly different, which might also require a slightly different nbgrader configuration.
If you run into problems getting nbgrader to work with JupyterHub, please do email the Jupyter mailing list!

Configuring JupyterHub
~~~~~~~~~~~~~~~~~~~~~~

To begin, we'll run a vanilla JuptyerHub with the following ``jupyterhub_config.py``:

.. literalinclude:: jupyterhub/jupyterhub_config.py
   :language: python

Then, you would run JupyterHub as follows. Note that in a real deployment, you
should generate your own auth token and keep it secret! For details on how to
do this, please refer to the JupyterHub documentation.

.. code:: bash

    export CONFIGPROXY_AUTH_TOKEN='foo'
    jupyterhub

Running this command should launch JupyterHub, which will then be accessible from
``localhost:8000``.


Configuring nbgrader formgrade
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make the formgrader integrate with JupyterHub, we must tell it to authenticate
users with JuptyerHub. The following is an example ``nbgrader_config.py`` that
does this:

.. literalinclude:: jupyterhub/nbgrader_config.py
   :language: python

In this example, the formgrader listens on localhost at port 9000, and uses the
special ``HubAuth`` authenticator class. This class tells the formgrader to ask
JupyterHub to route requests from ``localhost:8000/hub/nbgrader/example_course``
to the formgrader at ``localhost:9000``, and configures the formgrader to only
allow access from usernames specifed in the list of graders. In addition, it
tells JupyterHub where the root of the class files directory (where the formgrader
should be run from) is in relation to where the notebook server will run.

Then, to run the formgrader, we must set the auth token to be the same as the
one that we ran JupyterHub with (and note, as before, that you should generate
this auth token and keep it secret):

.. code:: bash

    export CONFIGPROXY_AUTH_TOKEN='foo'
    nbgrader formgrade

Running this command will launch the formgrader, which you should be able to
access from ``localhost:8000/hub/nbgrader/example_course``. If you properly
configured the ``notebook_url_prefix``, you should additionally be able to open
live notebooks from the formgrader using your notebook server that was spawned
by JupyterHub.
