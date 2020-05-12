import os
import shutil
import glob

from nbgrader.exchange.abc import ExchangeFetchFeedback as ABCExchangeFetchFeedback
from nbgrader.exchange.default import Exchange

from nbgrader.utils import check_mode, notebook_hash, make_unique_key, get_username


class ExchangeFetchFeedback(Exchange, ABCExchangeFetchFeedback):

    def init_src(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.coursedir.course_id)
        self.outbound_path = os.path.join(self.course_path, 'feedback')
        self.src_path = os.path.join(self.outbound_path)
        self.cache_path = os.path.join(self.cache, self.coursedir.course_id)

        if self.coursedir.student_id != '*':
            # An explicit student id has been specified on the command line; we use it as student_id
            if '*' in self.coursedir.student_id or '+' in self.coursedir.student_id:
                self.fail("The student ID should contain no '*' nor '+'; got {}".format(self.coursedir.student_id))
            student_id = self.coursedir.student_id
        else:
            student_id = get_username()

        if not os.path.isdir(self.src_path):
            self._assignment_not_found(
                self.src_path,
                os.path.join(self.outbound_path, "*"))
        if not check_mode(self.src_path, execute=True):
            self.fail("You don't have execute permissions for the directory: {}".format(self.src_path))

        assignment_id = self.coursedir.assignment_id if self.coursedir.assignment_id else '*'
        pattern = os.path.join(self.cache_path, '*+{}+*'.format(assignment_id))
        self.log.debug(
            "Looking for submissions with pattern: {}".format(pattern))

        self.feedback_files = []
        submissions = [os.path.split(x)[-1] for x in glob.glob(pattern)]
        for submission in submissions:
            _, assignment_id, timestamp = submission.split('/')[-1].split('+')
            self.log.debug(
                "Looking for feedback for '{}/{}' submitted at {}".format(
                    self.coursedir.course_id, assignment_id, timestamp))
            pattern = os.path.join(self.cache_path, submission, "*.ipynb")
            notebooks = glob.glob(pattern)
            for notebook in notebooks:
                notebook_id = os.path.splitext(os.path.split(notebook)[-1])[0]
                unique_key = make_unique_key(
                    self.coursedir.course_id,
                    assignment_id,
                    notebook_id,
                    student_id,
                    timestamp)

                # Look for the feedback using new-style of feedback
                self.log.debug("Unique key is: {}".format(unique_key))
                nb_hash = notebook_hash(notebook, unique_key)
                feedbackpath = os.path.join(self.outbound_path, '{0}.html'.format(nb_hash))
                if os.path.exists(feedbackpath):
                    self.feedback_files.append((notebook_id, timestamp, feedbackpath))
                    self.log.info(
                        "Found feedback for '{}/{}/{}' submitted at {}".format(
                            self.coursedir.course_id, assignment_id, notebook_id, timestamp))
                    continue

                # If it doesn't exist, try the legacy hashing
                nb_hash = notebook_hash(notebook)
                feedbackpath = os.path.join(self.outbound_path, '{0}.html'.format(nb_hash))
                if os.path.exists(feedbackpath):
                    self.feedback_files.append((notebook_id, timestamp, feedbackpath))
                    self.log.warning(
                        "Found legacy feedback for '{}/{}/{}' submitted at {}".format(
                            self.coursedir.course_id, assignment_id, notebook_id, timestamp))
                    continue

                # If we reached here, then there's no feedback available
                self.log.warning(
                    "Could not find feedback for '{}/{}/{}' submitted at {}".format(
                        self.coursedir.course_id, assignment_id, notebook_id, timestamp))

    def init_dest(self):
        if self.path_includes_course:
            root = os.path.join(self.coursedir.course_id, self.coursedir.assignment_id)
        else:
            root = self.coursedir.assignment_id
        self.dest_path = os.path.abspath(os.path.join(self.assignment_dir, root, 'feedback'))

    def do_copy(self, src, dest):
        for notebook_id, timestamp, feedbackpath in self.feedback_files:
            dest_with_timestamp = os.path.join(dest, timestamp)
            if not os.path.isdir(dest_with_timestamp):
                os.makedirs(dest_with_timestamp)
            new_name = notebook_id + '.html'
            html_file = os.path.join(dest_with_timestamp, new_name)
            self.log.debug("Copying feedback from {} to {}".format(feedbackpath, html_file))
            if os.path.exists(html_file):
                self.log.debug("Overwriting existing feedback: {}".format(html_file))
            shutil.copy(feedbackpath, html_file)
            self.log.info("Fetched feedback: {}".format(html_file))

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
