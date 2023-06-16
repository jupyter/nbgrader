"""Server configuration for integration tests.
!! Never use this configuration in production because it
opens the server to the world and provide access to JupyterLab
JavaScript objects through the global window variable.
"""
from pathlib import Path
import jupyterlab

c.ServerApp.port = 8888
c.ServerApp.port_retries = 0
c.ServerApp.open_browser = False

c.ServerApp.token = ""
c.ServerApp.password = ""
c.ServerApp.disable_check_xsrf = True

c.JupyterNotebookApp.expose_app_in_browser = True

c.LabServerApp.extra_labextensions_path = str(Path(jupyterlab.__file__).parent / "galata")

# Uncomment to set server log level to debug level
# c.ServerApp.log_level = "DEBUG"
