c = get_config()

# Add users here that are allowed admin access to JupyterHub.
c.Authenticator.admin_users = ["instructor1"]

# Add users here that are allowed to login to JupyterHub.
c.Authenticator.whitelist = [
    "instructor1", "instructor2", "student1", "student2", "student3"
]

# Add users here that are allowed to access the formgrader. NOTE: this option
# strictly adds users. If you want to revoke formgrader access after running
# JupyterHub, you will need to use the JupyterHub API to remove that user
# from the formgrader group.
c.JupyterHub.load_groups = {
    'formgrader': ['instructor1', 'instructor2']
}

# This is the key piece which defines how JupyterHub should talk to nbgrader
c.JupyterHub.services = [
    {
        'name': 'formgrader',
        'admin': True,
        'command': ['nbgrader', 'formgrade'],

        # This URL should match the IP address and port as it is set in
        # the nbgrader_config.py file
        'url': 'http://127.0.0.1:9000'
    }
]
