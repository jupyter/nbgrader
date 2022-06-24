c = get_config()

# Our user list
c.Authenticator.allowed_users = [
    'instructor1',
    'instructor2',
    'student1',
    'grader-course101',
    'grader-course123',
]

# instructor1 and instructor2 have access to different shared servers.
# Note that groups providing access to the formgrader *must* start with
# 'formgrade-', and groups providing access to course materials *must*
# start with 'nbgrader-' in order for nbgrader to work correctly.
c.JupyterHub.load_groups = {
    'instructors': [
        'instructor1',
        'instructor2',
    ],
    'formgrade-course101': [
        'instructor1',
        'grader-course101',
    ],
    'formgrade-course123': [
        'instructor2',
        'grader-course123',
    ],
    'nbgrader-course101': [
        'instructor1',
        'student1',
    ],
    'nbgrader-course123': [
        'instructor2',
        'student1',
    ],
}

c.JupyterHub.load_roles = roles = [
    {
        'name': 'instructor',
        'groups': ['instructors'],
        'scopes': [
            # these are the scopes required for the admin UI
            'admin:users',
            'admin:servers',
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
for course in ['course101', 'course123']:
    # access to formgrader
    roles.append(
        {
            'name': f'formgrade-{course}',
            'groups': [f'formgrade-{course}'],
            'scopes': [
                f'access:services!service={course}',
            ],
        }
    )
    # access to course materials
    roles.append(
        {
            'name': f'nbgrader-{course}',
            'groups': [f'nbgrader-{course}'],
            'scopes': [
                # access to the services API to discover the service(s)
                'list:services',
                f'read:services!service={course}',
            ],
        }
    )


# Start the notebook server as a service. The port can be whatever you want
# and the group has to match the name of the group defined above.
c.JupyterHub.services = [
    {
        'name': 'course101',
        'url': 'http://127.0.0.1:9999',
        'command': [
            'jupyterhub-singleuser',
            '--debug',
        ],
        'user': 'grader-course101',
        'cwd': '/home/grader-course101',
        'environment': {
            # specify formgrader as default landing page
            'JUPYTERHUB_DEFAULT_URL': '/formgrader'
        },
        'api_token': '{{course101_token}}',
    },
    {
        'name': 'course123',
        'url': 'http://127.0.0.1:9998',
        'command': [
            'jupyterhub-singleuser',
            '--debug',
        ],
        'user': 'grader-course123',
        'cwd': '/home/grader-course123',
        'environment': {
            # specify formgrader as default landing page
            'JUPYTERHUB_DEFAULT_URL': '/formgrader'
        },
        'api_token': '{{course123_token}}',
    },
]
