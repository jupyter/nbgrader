from IPython.config.loader import Config
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp

class AssignApp(CustomNbConvertApp):
    
    name = Unicode(u'nbgrader-assign')
    description = Unicode(u'Prepare a student version of an assignment by removing solutions')

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.IncludeHeaderFooter',
            'nbgrader.preprocessors.ClearSolutions',
            'IPython.nbconvert.preprocessors.ClearOutputPreprocessor'
        ]
        self.config.merge(self.extra_config)
