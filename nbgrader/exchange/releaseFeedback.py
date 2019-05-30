import os
import shutil
import glob
import hashlib
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISGID, ST_MODE
)

from traitlets import Bool

from .exchange import Exchange
from ..utils import self_owned, compute_checksum


class ExchangeReleaseFeedback(Exchange):

    def init_src(self):
        self.src_path = os.path.join(self.coursedir.root, self.coursedir.feedback_directory)

    def init_dest(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.course_id)
        self.outbound_feedback_path = os.path.join(self.course_path, 'feedback')
        self.dest_path = os.path.join(self.outbound_feedback_path)
        # 0755
        self.ensure_directory(
            self.outbound_feedback_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        )
    # should be moved up to Exchange? Common to this and release
    def ensure_directory(self, path, mode):
        """Ensure that the path exists, has the right mode and is self owned."""
        if not os.path.isdir(path):
            os.mkdir(path)
            # For some reason, Python won't create a directory with a mode of 0o733
            # so we have to create and then chmod.
            os.chmod(path, mode)
        else:
            if not self_owned(path):
                self.fail("You don't own the directory: {}".format(path))

    def copy_files(self):
        self.log.info("using src path: {}".format(self.src_path))
        for dirname, dirnames, _ in os.walk(self.src_path):
            for udir in dirnames:
                if udir == self.coursedir.assignment_id:
                    self.log.info("found directory {0} {1}".format( udir,os.path.join( dirname, udir)+'/*.html'))
                    timestamp = open(os.path.join( dirname, udir,'timestamp.txt')).read()
                    self.log.info("timestamp {}".format( timestamp ))
                    user = dirname.split('/')[-1]    
                    submissionDir = os.path.join( self.src_path , '../submitted/' , '{0}/{1}'.format(user,udir,timestamp) )
                    for html_file in glob.glob(os.path.join(dirname, udir)+'/*.html'):
                        fname = html_file.split('/')[-1].replace('.html','')
                        self.log.info("found html file {}".format( fname))
                        nbfile = "{0}/{1}.ipynb".format( submissionDir,fname)
                        m = hashlib.md5()
                        m.update(open(nbfile,'rb').read())
                        checksum = m.hexdigest()
                        dest = os.path.join(self.dest_path,checksum+'.html')
                        self.log.info(dest)
                        shutil.copy(html_file, dest)
