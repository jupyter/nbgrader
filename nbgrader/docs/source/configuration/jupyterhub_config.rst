Using nbgrader with JupyterHub
==============================

.. seealso::

    :doc:`/user_guide/creating_and_grading_assignments`
        Documentation for ``nbgrader assign``, ``nbgrader autograde``, ``nbgrader formgrade``, and ``nbgrader feedback``.

    :doc:`/user_guide/managing_assignment_files`
        Documentation for ``nbgrader release``, ``nbgrader fetch``, ``nbgrader submit``, and ``nbgrader collect``.

    :doc:`config_options`
        Details on ``nbgrader_config.py``

    :doc:`/user_guide/philosophy`
        More details on how the nbgrader hierarchy is structured.

    `JupyterHub Documentation <https://jupyterhub.readthedocs.io/en/latest/getting-started/index.html>`_
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
:doc:`/user_guide/creating_and_grading_assignments`) can be configured to
integrate with JupyterHub so that all grading can occur on the same server.

.. warning::

    The way that the formgrader integrates with JupyterHub changed between
    versions 0.4 and 0.5 in a backwards-incompatible way. However, this means
    that the formgrader should be much easier to use with JupyterHub!

.. warning::

    Starting in version 0.5.0 of nbgrader, the formgrader is no longer a
    standalone command. Rather, it is an extension of the Jupyter notebook.

Example Use Case: One Class, One Grader
---------------------------------------

The formgrader should work out-of-the-box with JupyterHub if you only have a
single grader for your class: all you need to do is make sure that you have
installed and enabled the nbgrader extensions (see
:doc:`/user_guide/installation`) and then make sure the path to your course
directory is properly set in the instructor's ``nbgrader_config.py``. For
example, if the instructor account is called ``instructor`` and your course
directory is located in ``/home/instructor/course101/``, then you should have
a file at ``/home/instructor/.jupyter/nbgrader_config.py`` with contents like:

.. code:: python

    c = get_config()
    c.CourseDirectory.root = '/home/instructor/course101'


Example Use Case: One Class, Multiple Graders
---------------------------------------------

If you have multiple graders, then you can set up a `shared notebook server
<https://github.com/jupyterhub/jupyterhub/tree/master/examples/service-notebook>`_
as a JupyterHub service. I recommend creating a separate grader account (such
as ``grader-course101``) for this server to have access to. Then, install and
enable the formgrader and Create Assignment extensions for this grader account
(see :doc:`/user_guide/installation`). Your JupyterHub config would then look
something like this:

.. code:: python

    c = get_config()

    # Our user list
    c.Authenticator.whitelist = [
        'instructor1',
        'instructor2',
        'student1',
    ]

    # instructor1 and instructor2 have access to a shared server:
    c.JupyterHub.load_groups = {
        'formgrader-course101': [
            'instructor1',
            'instructor2'
        ]
    }

    # Start the notebook server as a service. The port can be whatever you want
    # and the group has to match the name of the group defined above.
    c.JupyterHub.services = [
        {
            'name': 'course101',
            'url': 'http://127.0.0.1:9999',
            'command': [
                'jupyterhub-singleuser',
                '--group=formgrader-course101',
                '--debug',
            ],
            'user': 'grader-course101',
            'cwd': '/home/grader-course101'
        }
    ]

Similarly to the use case with just a single grader, there needs to then be a ``nbgrader_config.py`` file in the root of the grader account, which points to the directory where the class files are, e.g. in ``/home/grader-course101/.jupyter/nbgrader_config.py``:

.. code:: python

    c = get_config()
    c.CourseDirectory.root = '/home/grader-course101/course101'

Example Use Case: Multiple Classes
----------------------------------

As in the case of multiple graders for a single class, if you have multiple
classes on the same JupyterHub instance, then you will need to create multiple
services (one for each course) and corresponding accounts for each service
(with the nbgrader extensions enabled, see :doc:`/user_guide/installation`).
For example, you could have users ``grader-course101`` and
``grader-course123``. Your JupyterHub config would then look something like
this:

.. code:: python

    c = get_config()

    # Our user list
    c.Authenticator.whitelist = [
        'instructor1',
        'instructor2',
        'student1',
    ]

    # instructor1 and instructor2 have access to different shared servers:
    c.JupyterHub.load_groups = {
        'formgrader-course101': [
            'instructor1'
        ],
        'formgrader-course123': [
            'instructor2'
        ]
    }

    # Start the notebook server as a service. The port can be whatever you want
    # and the group has to match the name of the group defined above.
    c.JupyterHub.services = [
        {
            'name': 'course101',
            'url': 'http://127.0.0.1:9999',
            'command': [
                'jupyterhub-singleuser',
                '--group=formgrader-course101',
                '--debug',
            ],
            'user': 'grader-course101',
            'cwd': '/home/grader-course101'
        },
        {
            'name': 'course123',
            'url': 'http://127.0.0.1:9998',
            'command': [
                'jupyterhub-singleuser',
                '--group=formgrader-course123',
                '--debug',
            ],
            'user': 'grader-course123',
            'cwd': '/home/grader-course123'
        },
    ]

There also needs to be a ``nbgrader_config.py`` file in the root of each grader
account, which points to the directory where the class files are, e.g. in
``/home/grader-course101/.jupyter/nbgrader_config.py`` would be:

.. code:: python

    c = get_config()
    c.CourseDirectory.root = '/home/grader-course101/course101'

and ``/home/grader-course123/.jupyter/nbgrader_config.py`` would be:

.. code:: python

    c = get_config()
    c.CourseDirectory.root = '/home/grader-course123/course123'

You will also need to do some additional configuration on the student side. If
each student is enrolled in exactly one course, then you will need to provide
them a custom ``nbgrader_config.py`` which specifies that course. Alternately,
if students may be enrolled in multiple courses, you need to provide them a
custom ``nbgrader_config.py`` that will cause nbgrader to look for assignments
in a subdirectory corresponding to the course name. See :ref:`multiple-classes`
for details.
