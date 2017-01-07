from nbgrader.apps import FormgradeApp
from traitlets.config import Config


def load_jupyter_server_extension(nbapp):
    """Load the formgrader extension"""

    webapp = nbapp.web_app

    # we need to set a few special config options for the formgrader to
    # work correctly -- the authentication mechanism, the relevant ip and port,
    # and the base url of the notebook server
    c = Config()
    c.FormgradeApp.authenticator_class = 'nbgrader.auth.NotebookAuth'
    c.FormgradeApp.ip = nbapp.ip
    c.FormgradeApp.port = nbapp.port
    c.NotebookAuth.notebook_base_url = nbapp.base_url
    c.NbGrader.log_level = nbapp.log_level

    # create the formgrader application
    formgrader = FormgradeApp(parent=nbapp)
    formgrader.update_config(c)
    super(FormgradeApp, formgrader).initialize([])
    formgrader.init_tornado_settings()
    formgrader.init_handlers()
    formgrader.print_status()

    # insert the handlers to the notebook application
    webapp.add_handlers(".*$", formgrader.handlers)

    # update settings
    formgrader.tornado_settings['nbgrader_mathjax_url'] = webapp.settings['mathjax_url']
    formgrader.tornado_settings['log_function'] = webapp.settings['log_function']
    webapp.settings.update(formgrader.tornado_settings)
