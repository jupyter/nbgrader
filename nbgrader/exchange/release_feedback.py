import os
import shutil
import glob
from stat import S_IRUSR, S_IWUSR, S_IXUSR, S_IXGRP, S_IXOTH

from .exchange import Exchange
from ..utils import notebook_hash


class ExchangeReleaseFeedback(Exchange):

    def init_src(self):
        self.src_path = os.path.join(self.coursedir.root, self.coursedir.feedback_directory)

    def init_dest(self):
        if self.coursedir.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.coursedir.course_id)
        self.outbound_feedback_path = os.path.join(self.course_path, 'feedback')
        self.dest_path = os.path.join(self.outbound_feedback_path)
        # 0755
        self.ensure_directory(
            self.outbound_feedback_path,
            S_IRUSR | S_IWUSR | S_IXUSR | S_IXGRP | S_IXOTH
        )

    def copy_files(self):
        self.log.info("using src path: {}".format(self.src_path))
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'
        self.log.info("student_id: {}".format(student_id))
        html_files = glob.glob(os.path.join(self.src_path, student_id, self.coursedir.assignment_id, '*.html'))
        self.log.info("html_files: {}".format(html_files))
        for html_file in html_files:
            assignment_dir, file_name = os.path.split(html_file)
            timestamp = open(os.path.join(assignment_dir, 'timestamp.txt')).read()
            self.log.info("timestamp {}".format(timestamp))
            user = assignment_dir.split('/')[-2]
            submissionDir = os.path.join(self.src_path, '../submitted/', '{0}/{1}'.format(user, self.coursedir.assignment_id))
            fname, _ = os.path.splitext(file_name.replace('.html', ''))
            self.log.info("found html file {}".format(fname))
            nbfile = "{0}/{1}.ipynb".format(submissionDir, fname)
            checksum = notebook_hash(nbfile)
            dest = os.path.join(self.dest_path, checksum + '.html')
            self.log.info(dest)
            shutil.copy(html_file, dest)
