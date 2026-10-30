import os
import shutil
from stat import S_IRUSR, S_IWUSR, S_IXUSR, S_IRGRP, S_IWGRP, S_IXGRP, S_IXOTH, S_ISGID

from nbgrader.exchange.abc import ExchangeReleaseFeedback as ABCExchangeReleaseFeedback
from .exchange import Exchange
from nbgrader.utils import notebook_hash


class ExchangeReleaseFeedback(Exchange, ABCExchangeReleaseFeedback):

    def init_src(self):
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'
        self.src_path = self.coursedir.format_path(
            self.coursedir.feedback_directory, student_id,
            self.coursedir.assignment_id)

    def init_dest(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.coursedir.course_id)
        self.outbound_feedback_path = os.path.join(self.course_path, 'feedback')
        self.dest_path = os.path.join(self.outbound_feedback_path)
        # 0755
        self.ensure_directory(
            self.outbound_feedback_path,
            (S_IRUSR | S_IWUSR | S_IXUSR | S_IXGRP | S_IXOTH |
             ((S_IRGRP|S_IWGRP|S_ISGID) if self.coursedir.groupshared else 0))
        )

    def copy_files(self):
        if self.coursedir.student_id_exclude:
            exclude_students = set(self.coursedir.student_id_exclude.split(','))
        else:
            exclude_students = set()

        for feedback in self.coursedir.find_notebooks(
            nbgrader_step=self.coursedir.feedback_directory,
            student_id=self.coursedir.student_id or "*",
            assignment_id=self.coursedir.assignment_id,
            notebook_id="*",
            ext="html"
        ):
            html_file = feedback['path']
            student_id = feedback['student_id']
            if student_id in exclude_students:
                self.log.debug("Skipping student '{}'".format(student_id))
                continue

            notebook_id = feedback['notebook_id']
            feedback_dir = html_file.parent

            timestamp = feedback_dir.joinpath('timestamp.txt').read_text()
            submission_secret = feedback_dir.joinpath("submission_secret.txt").read_text()

            checksum = notebook_hash(secret=submission_secret, notebook_id=notebook_id)
            dest = os.path.join(self.dest_path, "{}-tmp.html".format(checksum))

            self.log.info(
                "Releasing feedback for student '%s' on assignment '%s/%s/%s' (%s)",
                student_id,
                self.coursedir.course_id,
                feedback["assignment_id"],
                notebook_id,
                timestamp
            )

            shutil.copy(html_file, dest)
            # Copy to temporary location and mv to update atomically.
            updated_feedback = os.path.join(self.dest_path, "{}.html". format(checksum))
            shutil.move(dest, updated_feedback)
            self.log.info("Feedback released to: {}".format(dest))
