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
        Fetch feedback for an assignment, if an instructor has released it.
        For the usage of students.

        You can run this command from any directory, but usually, you will run
        it from the directory where you are keeping your course assignments.

        To fetch an assignment by name into the current directory:

            nbgrader fetch_feedback assignment1

        To fetch the assignment for a specific course (or if your course_id is
        not set in a configuration file already), you must first know the
        `course_id` for your course.  If you don't know it, ask your
        instructor.  Then, simply include the argument with the '--course'
        flag:

            nbgrader fetch_feedback assignment1 --course=phys101

        This will create a new `feedback` directory within the corresponding
        assignment directory with the feedback inside.  There can be multiple
        feedbacks if you submitted multiple times and the instructor generated
        it multiple times.
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
            self.fail("Must provide assignment name:\nnbgrader fetch_feedback ASSIGNMENT [ --course COURSE ]")

        if self.coursedir.assignment_id != "":
            fetch = ExchangeFetchFeedback(
                coursedir=self.coursedir,
                authenticator=self.authenticator,
                parent=self)
            try:
                fetch.start()
            except ExchangeError:
                self.fail("nbgrader fetch_feedback failed")
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
                self.fail("nbgrader fetch_feedback failed")
