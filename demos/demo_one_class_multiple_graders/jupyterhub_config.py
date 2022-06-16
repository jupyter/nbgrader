c = get_config()

# Our user list
c.Authenticator.allowed_users = [
    'instructor1',
    'instructor2',
    'student1',
]

# instructor1 and instructor2 have access to a shared server.
# This group *must* start with formgrade- for nbgrader to work correctly.
c.JupyterHub.load_groups = {
    'formgrade-course101': [
        'instructor1',
        'instructor2',
    ]
}

# Note: we don't need to add students to a nbgrader-course101 group to give
# them access to coure materials (as we do in demo_multiple_classes) because
# we explicitly set the course id in the nbgrader_config.py. If we didn't
# set this explicitly, we would also have to create a nbgrader-course101
# group and give it the scopes of:
# ['list:services', 'read:services!service=course101'].

c.JupyterHub.load_roles = [
    {
        'name': 'formgrade-course101',
        'groups': ['formgrade-course101'],
        'scopes': [
            'access:services!service=course101',
            # access to the services API to discover the service(s)
            'list:services',
            f'read:services!service=course101',
        ],
    },
    # The class_list extension needs permission to access services
    {
        'name': 'server',
        'scopes': [
            'inherit',
            # in JupyterHub 2.4, this can be a list of permissions
            # greater than the owner and the result will be the intersection;
            # until then, 'inherit' is the only way to have variable permissions
            # for the server token by user
            # "access:services",
            # "list:services",
            # "read:services",
            # "users:activity!user",
            # "access:servers!user",
        ],
    },
]

# Start the notebook server as a service. The port can be whatever you want
# and the group has to match the name of the group defined above. The name of
# the service MUST match the name of your course.
c.JupyterHub.services = [
    {
        'name': 'course101',
        'url': 'http://127.0.0.1:9999',
        'command': [
            'jupyterhub-singleuser',
            '--debug',
        ],
        'user': 'grader-course101',
        'environment': {
            # specify formgrader as default landing page
            'JUPYTERHUB_DEFAULT_URL': '/formgrader'
        },
        'cwd': '/home/grader-course101',
    }
]
