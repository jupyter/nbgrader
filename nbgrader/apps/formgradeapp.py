from IPython.config.loader import Config
from IPython.config.application import catch_config_error
from IPython.utils.traitlets import Unicode

from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags
from nbgrader.templates import get_template, get_template_path


aliases = {}
aliases.update(base_aliases)
aliases.update({
    'form-id': 'GForm.form_id',
    'regexp': 'FindStudentID.regexp'
})

flags = {}
flags.update(base_flags)
flags.update({
})


class FormgradeApp(CustomNbConvertApp):
    
    name = Unicode(u'nbgrader-formgrade')
    description = Unicode(u'Grade a notebook using a Google Form')
    aliases = aliases
    flags = flags

    student_id = Unicode(u'', config=True)

    def _export_format_default(self):
        return 'html'

    def build_extra_config(self):
        self.extra_config = Config()
        self.extra_config.Exporter.preprocessors = [
            'nbgrader.preprocessors.FindStudentID'
        ]
        self.extra_config.Exporter.template_file = 'formgrade'
        self.extra_config.Exporter.template_path = ['.', get_template_path()]
        self.config.merge(self.extra_config)
