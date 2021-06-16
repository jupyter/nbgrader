import os

from traitlets.config import Config
from traitlets import List, default
from nbconvert.exporters import HTMLExporter
from nbconvert.preprocessors import CSSHTMLHeaderPreprocessor

from .base import BaseConverter
from ..preprocessors import GetGrades


class GenerateFeedback(BaseConverter):

    @property
    def _input_directory(self):
        return self.coursedir.autograded_directory

    @property
    def _output_directory(self):
        return self.coursedir.feedback_directory

    preprocessors = List([
        GetGrades,
        CSSHTMLHeaderPreprocessor
    ]).tag(config=True)

    @default("classes")
    def _classes_default(self):
        classes = super(GenerateFeedback, self)._classes_default()
        classes.append(HTMLExporter)
        return classes

    @default("export_class")
    def _exporter_class_default(self):
        return HTMLExporter

    @default("permissions")
    def _permissions_default(self):
        return 664 if self.coursedir.groupshared else 644

    def _load_config(self, cfg, **kwargs):
        if 'Feedback' in cfg:
            self.log.warning(
                "Use GenerateFeedback in config, not Feedback. Outdated config:\n%s",
                '\n'.join(
                    'Feedback.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.GenerateFeedbackApp.items()
                )
            )
            cfg.GenerateFeedback.merge(cfg.Feedback)
            del cfg.Feedback

        super(GenerateFeedback, self)._load_config(cfg, **kwargs)

    def __init__(self, coursedir=None, **kwargs):
        super(GenerateFeedback, self).__init__(coursedir=coursedir, **kwargs)
        c = Config()
        c.HTMLExporter.template_name = 'feedback'
        c.HTMLExporter.template_file = 'feedback.html.j2'
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server_extensions', 'formgrader', 'templates'))
        c.HTMLExporter.extra_template_basedirs.append(template_path)
        self.update_config(c)
