from IPython.config.loader import Config
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp

class SolutionApp(CustomNbConvertApp):
    
    name = Unicode(u'nbgrader-solution')
    description = Unicode(u'Prepare a solution version of an assignment')

    def _export_format_default(self):
        return 'notebook'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.IncludeHeaderFooter',
            'nbgrader.preprocessors.TableOfContents',
            'nbgrader.preprocessors.RenderSolutions',
            'nbgrader.preprocessors.ExtractTests',
            'IPython.nbconvert.preprocessors.ExecutePreprocessor'
        ]
        self.extra_config.RenderSolutions.solution = True
        self.extra_config.NbGraderApp.writer_class = 'IPython.nbconvert.writers.FilesWriter'
        self.config.merge(self.extra_config)
