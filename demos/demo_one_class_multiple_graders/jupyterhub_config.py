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
# and the group has to match the name of the group defined above. The name of
# the service MUST match the name of your course.
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

