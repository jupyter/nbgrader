c = get_config()

# Our user list
c.Authenticator.allowed_users = [
    'instructor1',
    'instructor2',
    'student1',
    'grader-course101',
    'grader-course123',
]

# instructor1 and instructor2 have access to different shared servers:
c.JupyterHub.load_groups = {
    'instructors': [
        'instructor1',
        'instructor2',
    ],
    'formgrader-course101': [
        'instructor1',
        'grader-course101',
    ],
    'formgrader-course123': [
        'instructor2',
        'grader-course123',
    ],
    'nbgrader-course101': [],
    'nbgrader-course123': [],
}

c.JupyterHub.load_roles = roles = []

roles.append(
    {
        'name': 'instructor',
        'groups': ['instructors'],
        'scopes': [
            # these are the scopes required for the admin UI
            'admin:users',
            'admin:servers',
        ],
    }
)
# add grader roles
for course in ['course101', 'course123']:
    roles.append(
        {
            'name': f'formgrader-{course}',
            'groups': [f'formgrader-{course}'],
            'scopes': [
                f'access:services!service={course}',
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
