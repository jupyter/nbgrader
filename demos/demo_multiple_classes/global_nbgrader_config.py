from nbgrader.auth import JupyterHubAuthPlugin
c = get_config()
c.Authenticator.plugin_class = JupyterHubAuthPlugin

