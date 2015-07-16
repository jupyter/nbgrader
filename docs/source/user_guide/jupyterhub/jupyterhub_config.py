c = get_config()

# Add users here that are allowed admin access to JupyterHub.
c.Authenticator.admin_users = ["jhamrick"]

# Add users here that are allowed to login to JupyterHub.
c.Authenticator.whitelist = ["jhamrick"]
