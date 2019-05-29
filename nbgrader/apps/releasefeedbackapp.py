# coding: utf-8

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeReleaseFeedback, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'force': (
        {'ExchangeReleaseFeedback' : {'force' : True}},
        "Force overwrite of existing files in the feedback exchange directory."
    ),
    'f': (
        {'ExchangeReleaseFeedback' : {'force' : True}},
        "Force overwrite of existing files in the feedback exchange directory."
    ),
})

class ReleaseFeedbackApp(NbGrader):

    name = u'nbgrader-release-feedback'
    description = u'Release assignment feedback to the nbgrader feedback exchange'

    aliases = aliases
    flags = flags

    examples = """
        write this when it works...
        """

    @default("classes")
    def _classes_default(self):
        classes = super(ReleaseFeedbackApp, self)._classes_default()
        classes.extend([Exchange, ExchangeReleaseFeedback])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'ReleaseFeedbackApp' in cfg:
            self.log.warning(
                "Use ExchangeReleaseFeedback in config, not ReleaseFeedbackApp. Outdated config:\n%s",
                '\n'.join(
                    'ReleaseFeedbackApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.ReleaseApp.items()
                )
            )
            cfg.ExchangeReleaseFeedback.merge(cfg.ReleaseFeedbackApp)
            del cfg.ReleaseFeedbackApp

        super(ReleaseFeedbackApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(ReleaseFeedbackApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        release = ExchangeReleaseFeedback(coursedir=self.coursedir, parent=self)
        try:
            release.start()
        except ExchangeError:
            self.fail("nbgrader release failed")
