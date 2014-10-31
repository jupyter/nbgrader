from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode
from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags


aliases = {}
aliases.update(base_aliases)
aliases.update({
    'header': 'IncludeHeaderFooter.header',
    'footer': 'IncludeHeaderFooter.footer'
})

flags = {}
flags.update(base_flags)
flags.update({
})


class AssignApp(CustomNbConvertApp):

    name = Unicode(u'nbgrader-assign')
    description = Unicode(u'Prepare a student version of an assignment by removing solutions')
    aliases = aliases
    flags = flags

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
