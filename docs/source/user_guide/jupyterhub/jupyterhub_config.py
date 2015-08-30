c = get_config()

# Add users here that are allowed admin access to JupyterHub.
c.Authenticator.admin_users = ["instructor1"]

# Add users here that are allowed to login to JupyterHub.
c.Authenticator.whitelist = [
    "instructor1", "instructor2", "student1", "student2", "student3"
]
