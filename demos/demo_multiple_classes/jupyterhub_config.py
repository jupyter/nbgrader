c = get_config()

# Our user list
c.Authenticator.whitelist = [
    'instructor1',
    'instructor2',
    'student1',
    'grader-course101',
    'grader-course123'
]

c.Authenticator.admin_users = {
    'instructor1',
    'instructor2'
}

# instructor1 and instructor2 have access to different shared servers:
c.JupyterHub.load_groups = {
    'formgrade-course101': [
        'instructor1',
        'grader-course101',
    ],
    'formgrade-course123': [
        'instructor2',
        'grader-course123'
    ],
    'nbgrader-course101': [],
    'nbgrader-course123': []
}

# Start the notebook server as a service. The port can be whatever you want
# and the group has to match the name of the group defined above.
c.JupyterHub.services = [
    {
        'name': 'course101',
        'url': 'http://127.0.0.1:9999',
        'command': [
            'jupyterhub-singleuser',
            '--group=formgrade-course101',
            '--debug',
        ],
        'user': 'grader-course101',
        'cwd': '/home/grader-course101',
        'api_token': '{{course101_token}}'
    },
    {
        'name': 'course123',
        'url': 'http://127.0.0.1:9998',
        'command': [
            'jupyterhub-singleuser',
            '--group=formgrade-course123',
            '--debug',
        ],
        'user': 'grader-course123',
        'cwd': '/home/grader-course123',
        'api_token': '{{course123_token}}'
    },
]

