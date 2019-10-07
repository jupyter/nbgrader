# coding: utf-8

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeReleaseFeedback, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "CourseDirectory.course_id",
})

flags = {}
flags.update(nbgrader_flags)

class ReleaseFeedbackApp(NbGrader):

    name = u'nbgrader-release-feedback'
    description = u'Release assignment feedback to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Release feedback for an assignment to students. For the usage of instructors.

        This command is run from the top-level nbgrader folder.

        The command releases the feedback present in the `feedback` folder. To populate
        this folder use the `nbgrader generate_feedback` command.

        To release the feedback for an assignment named `assignment1` run:

            nbgrader release_feedback assignment1

        Release feedback overrides existing files. It should not be a problem given
        that the feedback is associated with the hash of hte notebook. Any new notebook
        will map to a different file. The only way a file actually gets replaced is when
        the same input notebook gets re-graded and in these cases one would want the latest
        grading to be the right one.

        """
    @default("classes")
    def _classes_default(self):
        classes = super(ReleaseFeedbackApp, self)._classes_default()
        classes.extend([Exchange, ExchangeReleaseFeedback])
        return classes

    def start(self):
        super(ReleaseFeedbackApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        release_feedback = self.exchange.ReleaseFeedback(
            coursedir=self.coursedir,
            authenticator=self.authenticator,
            parent=self)
        try:
            release_feedback.start()
        except ExchangeError:
            self.fail("nbgrader release_feedback failed")
