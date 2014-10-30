from IPython.config.loader import Config
from IPython.utils.traitlets import Unicode

from nbgrader.apps.customnbconvertapp import CustomNbConvertApp
from nbgrader.apps.customnbconvertapp import aliases as base_aliases
from nbgrader.apps.customnbconvertapp import flags as base_flags
from nbgrader.templates import get_template_path


aliases = {}
aliases.update(base_aliases)
aliases.update({
    'regexp': 'FindStudentID.regexp'
})

flags = {}
flags.update(base_flags)
flags.update({
    'serve': (
        {'FormgradeApp': {'postprocessor_class': 'nbgrader.postprocessors.ServeFormGrader'}},
        "Run the form grading server"
    )
})


class FormgradeApp(CustomNbConvertApp):

    name = Unicode(u'nbgrader-formgrade')
    description = Unicode(u'Grade a notebook using an HTML form')
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
