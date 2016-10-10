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
collect`` commands (see :doc:`/user_guide/managing_assignment_files`) with a shared server
setup like JupyterHub, the formgrader (see
:doc:`/user_guide/creating_and_grading_assignments`) can be configured to integrate with
JupyterHub so that all grading can occur on the same server.

To set up the formgrader to work with JupyterHub, you will need to specify a
few custom config options (see :doc:`config_options` for details on all possible config options, and where configuration files live).
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
allow access from usernames specified in the list of graders. In addition, it
tells JupyterHub where the root of the class files directory (where the formgrader
should be run from) is in relation to where the notebook server will run.

Then, to run the formgrader, we must set the auth token to be the same as the
one that we ran JupyterHub with (and note, as before, that you should generate
this auth token and keep it secret):

.. code:: bash

    export CONFIGPROXY_AUTH_TOKEN='foo'
    export JPY_API_TOKEN=$(jupyterhub token --db=sqlite:///path/to/jupyterhub.sqlite -f /path/to/jupyterhub_config <user>)

where ``<user>`` should be the username of a JupyterHub admin user,
``sqlite:///path/to/jupyterhub.sqlite`` is the path to the JupyterHub database
(e.g. ``sqlite:///jupyterhub.sqlite``), and ``/path/to/jupyterhub_config`` is
the path to your ``jupyterhub_config.py`` file. This will store the API token
in an environment variable called ``JPY_API_TOKEN``, which we'll use later.

Now that we've set the auth token and the API token, we can launch the
formgrader:

.. code:: bash

    nbgrader formgrade

Running this command will launch the formgrader, which you should be able to
access from ``localhost:8000/hub/nbgrader/example_course``. If you properly
configured the ``notebook_url_prefix``, you should additionally be able to open
live notebooks from the formgrader using your notebook server that was spawned
by JupyterHub.

Configuring SSL
~~~~~~~~~~~~~~~

You should almost certainly be running JupyterHub with SSL support, as it is
insecure to not do so. However, this requires a bit more additional
configuration on the nbgrader side as well. In particular, you will need to change the ``HubAuth.hub_base_url`` config option to include ``https``:

.. code:: python

    c.HubAuth.hub_base_url = "https://localhost:443"

For a minimal working example of using JupyterHub with SSL, please see the
``nbgrader.tests.formgrader.manager.HubAuthSSLManager`` in the `nbgrader tests
<https://github.com/jupyter/nbgrader/blob/master/nbgrader/tests/formgrader/manager.py>`__.
