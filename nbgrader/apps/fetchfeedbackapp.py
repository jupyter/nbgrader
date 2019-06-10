# coding: utf-8

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeFetchFeedback, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "CourseDirectory.course_id",
})

flags = {}
flags.update(nbgrader_flags)


class FetchFeedbackApp(NbGrader):

    name = u'nbgrader-fetch-feedback'
    description = u'Fetch feedback for an assignment from the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Fetch feedback for an assignment that an instructor has released. MORE INFO NEEDED
        For the usage of students.

        You can run this command from any directory, but usually, you will have a
        directory where you are keeping your course assignments.

        To fetch an assignment by name into the current directory:

            nbgrader fetch assignment1

        To fetch an assignment for a specific course, you must first know the
        `course_id` for your course.  If you don't know it, ask your instructor.
        Then, simply include the argument with the '--course' flag.

            nbgrader fetch assignment1 --course=phys101

        This will create an new directory named `assignment1` where you can work
        on the assignment. When you are done, use the `nbgrader submit` command
        to turn in the assignment.
        """

    @default("classes")
    def _classes_default(self):
        classes = super(FetchFeedbackApp, self)._classes_default()
        classes.extend([Exchange, ExchangeFetchFeedback])
        return classes

    def start(self):
        super(FetchFeedbackApp, self).start()

        # set assignment and course
        if len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        if self.coursedir.assignment_id != "":
            fetch = ExchangeFetchFeedback(
                coursedir=self.coursedir,
                authenticator=self.authenticator,
                parent=self)
            try:
                fetch.start()
            except ExchangeError:
                self.fail("nbgrader fetch failed")
        else:
            failed = False

            for arg in self.extra_args:
                self.coursedir.assignment_id = arg
                fetch = ExchangeFetchFeedback(
                    coursedir=self.coursedir,
                    authenticator=self.authenticator,
                    parent=self)
                try:
                    fetch.start()
                except ExchangeError:
                    failed = True

            if failed:
                self.fail("nbgrader fetchfeedback failed")
