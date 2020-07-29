from ._version import __version__ 
from .handlers import setup_handlers


def _jupyter_server_extension_paths():
    return [{
        "module": "assignment_list"
    }]


def load_jupyter_server_extension(lab_app):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    lab_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    setup_handlers(lab_app)
    lab_app.log.info("Registered HelloWorld extension at URL path /assignment_list")
