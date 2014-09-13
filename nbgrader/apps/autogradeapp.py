from IPython.config.loader import Config
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp

class AutogradeApp(CustomNbConvertApp):
    
    name = Unicode(u'nbgrader-autograde')
    description = Unicode(u'Autograde a notebook by running it')

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor',
            'IPython.nbconvert.preprocessors.ExecutePreprocessor',
        ]
        self.config.merge(self.extra_config)

