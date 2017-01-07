c = get_config()

# Add users here that are allowed admin access to JupyterHub.
c.Authenticator.admin_users = ["instructor1"]

# Add users here that are allowed to login to JupyterHub.
c.Authenticator.whitelist = [
    "instructor1", "instructor2", "student1", "student2", "student3"
]

# Add users here that are allowed to access the formgrader. You can add as as
# many groups here as you'd like, for as many classes as you are using nbgrader
# with.
#
# NOTE: this option strictly adds users. If you want to revoke formgrader access
# after running JupyterHub, you will need to use the JupyterHub API to remove
# that user from the relevant group.
c.JupyterHub.load_groups = {
    'course101-graders': ['instructor1', 'instructor2']
}

# This is the key piece which defines how JupyterHub should talk to nbgrader
c.JupyterHub.services = [
    {
        # This is the name of the service, which will be accessible at
        # yourdomain.com/services/<name>. You can customize this to be unique
        # for your class, so that you can run multiple instances of the
        # formgrader.
        'name': 'formgrader-course101',
        'admin': True,
        'command': ['nbgrader', 'formgrade'],

        # This URL should match the IP address and port as it is set in
        # the nbgrader_config.py file.
        'url': 'http://127.0.0.1:9000',

        # This should be the full path to where the nbgrader directory lives.
        'cwd': '/path/to/nbgrader/directory'
    }
]
