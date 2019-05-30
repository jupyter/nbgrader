import os
import shutil
import glob

from traitlets import Bool

from .exchange import Exchange
from ..utils import check_mode, notebook_hash


class ExchangeFetchFeedback(Exchange):

    def init_src(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.root, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'feedback')
        self.src_path = os.path.join(self.outbound_path)
        if not os.path.isdir(self.src_path):
            self._assignment_not_found(
                self.src_path,
                os.path.join(self.outbound_path, "*"))
        if not check_mode(self.src_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.src_path))
        assignment_id = self.coursedir.assignment_id if self.coursedir.assignment_id else '*'
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'
        pattern = os.path.join(self.root, self.course_id, 'inbound', '{}+{}+*/*.ipynb'.format(student_id, assignment_id))
        notebooks = glob.glob(pattern)
        self.log.info(notebooks)
        self.feedbackFiles = []
        for notebook in notebooks:
            directory, nbname = os.path.split(notebook)
            timestamp = directory.split('/')[-1].split('+')[2]
            nb_hash = notebook_hash(notebook)
            feedbackpath = os.path.join(self.root, self.course_id, 'feedback','{0}.html'.format(nb_hash))  
            if os.path.exists(feedbackpath):
                self.feedbackFiles.append( (nbname, timestamp, feedbackpath))
                

    def init_dest(self):
        if self.path_includes_course:
            root = os.path.join(self.course_id, self.coursedir.assignment_id)
        else:
            root = self.coursedir.assignment_id
        self.dest_path = os.path.abspath(os.path.join('.', root,'feedback'))
        
    def copy_if_missing(self, src, dest, ignore=None):

        for nbname, timestamp, feedbackpath in self.feedbackFiles:
            srcpath = os.path.join(src, filename)
            destpath = os.path.join(dest, filename)
            relpath = os.path.relpath(destpath, os.getcwd())
            if not os.path.exists(destpath):
                if os.path.isdir(srcpath):
                    self.log.warning("Creating missing directory '%s'", relpath)
                    os.mkdir(destpath)

                else:
                    self.log.warning("Replacing missing file '%s'", relpath)
                    shutil.copy(srcpath, destpath)

            if os.path.isdir(srcpath):
                self.copy_if_missing(srcpath, destpath, ignore=ignore)

    def do_copy(self, src, dest):
        for nbname, timestamp, feedbackpath in self.feedbackFiles:
            self.log.info( '{}'.format( (nbname, timestamp, feedbackpath) ) )
            destWithTimestamp = os.path.join(dest,timestamp)    
            if not os.path.isdir(destWithTimestamp):
                os.makedirs(destWithTimestamp)
            noExt, _ = os.path.splitext(nbname)
            newName = noExt + '.html'
            htmlFile = os.path.join(destWithTimestamp, newName)
            shutil.copy(feedbackpath, htmlFile)
        #else:
        #    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.coursedir.ignore))

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Fetched as: {} {}".format(self.course_id, self.coursedir.assignment_id))
