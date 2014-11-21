from IPython.utils.traitlets import Unicode, List
from IPython.core.application import BaseIPythonApplication
from IPython.core.application import base_aliases, base_flags
from IPython.config.application import catch_config_error
from IPython.core.profiledir import ProfileDir

import os
import shutil
import tempfile
import datetime
import tarfile
import glob
import logging

from textwrap import dedent

aliases = {}
aliases.update(base_aliases)
aliases.update({
    "assignment": "SubmitApp.assignment_name",
    "submit-dir": "SubmitApp.submissions_directory"
})

flags = {}
flags.update(base_flags)
flags.update({
})

examples = """
nbgrader submit "Problem Set 1/"
nbgrader submit "Problem Set 1/" --assignment ps01
"""

class SubmitApp(BaseIPythonApplication):

    name = Unicode(u'nbgrader-submit')
    description = Unicode(u'Submit a completed assignment')
    aliases = aliases
    flags = flags
    examples = examples

    student = Unicode(os.environ['USER'])
    timestamp = Unicode(str(datetime.datetime.now()))
    assignment_directory = Unicode(
        '.', config=True, 
        help=dedent(
            """
            The directory containing the assignment to be submitted.
            """
        )
    )
    assignment_name = Unicode(
        '', config=True, 
        help=dedent(
            """
            The name of the assignment. Defaults to the name of the assignment
            directory.
            """
        )
    )
    submissions_directory = Unicode(
        "{}/.submissions".format(os.environ['HOME']), config=True, 
        help=dedent(
            """
            The directory where the submission will be saved.
            """
        )
    )

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc"
        ], 
        config=True,
        help=dedent(
            """
            List of file names or file globs to be ignored when creating the
            submission.
            """
        )
    )

    # The classes added here determine how configuration will be documented
    classes = List()
    def _classes_default(self):
        """This has to be in a method, for TerminalIPythonApp to be available."""
        return [
            ProfileDir
        ]

    def _log_level_default(self):
        return logging.INFO

    @catch_config_error
    def initialize(self, argv=None):
        if not os.path.exists(self.ipython_dir):
            self.log.warning("Creating IPython directory: {}".format(self.ipython_dir))
            os.mkdir(self.ipython_dir)
        super(SubmitApp, self).initialize(argv)
        self.stage_default_config_file()
        self.init_assignment_root()

        if self.assignment_name == '':
            self.assignment_name = os.path.basename(self.assignment_directory)

    def init_assignment_root(self):
        # Specifying notebooks on the command-line overrides (rather than adds)
        # the notebook list
        if self.extra_args:
            patterns = self.extra_args
        else:
            patterns = [self.assignment_directory]

        if len(patterns) == 0:
            pass

        elif len(patterns) == 1:
            self.assignment_directory = patterns[0]

        else:
            raise ValueError("You must specify the name of a directory")

        self.assignment_directory = os.path.abspath(self.assignment_directory)

        if not os.path.isdir(self.assignment_directory):
            raise ValueError("Path is not a directory: {}".format(self.assignment_directory))

    def _is_ignored(self, filename):
        dirname = os.path.dirname(filename)
        for expr in self.ignore:
            globs = glob.glob(os.path.join(dirname, expr))
            if filename in globs:
                self.log.debug("Ignoring file: {}".format(filename))
                return True
        return False

    def make_temp_copy(self):
        """Copy the submission to a temporary directory. Returns the path to the
        temporary copy of the submission."""
        # copy everything to a temporary directory
        pth = os.path.join(self.tmpdir, self.assignment_name)
        shutil.copytree(self.assignment_directory, pth)
        os.chdir(self.tmpdir)

        # get the user name, write it to file
        with open(os.path.join(self.assignment_name, "user.txt"), "w") as fh:
            fh.write(self.student)

        # save the submission time
        with open(os.path.join(self.assignment_name, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        return pth

    def make_archive(self, path_to_submission):
        """Make a tarball of the submission. Returns the path to the created
        archive."""
        root, submission = os.path.split(path_to_submission)
        os.chdir(root)

        archive = os.path.join(self.tmpdir, "{}.tar.gz".format(self.assignment_name))
        tf = tarfile.open(archive, "w:gz")

        for (dirname, dirnames, filenames) in os.walk(submission):
            if self._is_ignored(dirname):
                continue

            for filename in filenames:
                pth = os.path.join(dirname, filename)
                if not self._is_ignored(pth):
                    self.log.debug("Adding '{}' to submission".format(pth))
                    tf.add(pth)

        tf.close()
        return archive

    def submit(self, path_to_tarball):
        """Submit the assignment."""
        archive = "{}.tar.gz".format(self.assignment_name)
        target = os.path.join(self.submissions_directory, archive)
        shutil.copy(path_to_tarball, target)

    def start(self):
        super(SubmitApp, self).start()
        self.tmpdir = tempfile.mkdtemp()
        
        try:
            path_to_submission = self.make_temp_copy()
            path_to_tarball = self.make_archive(path_to_submission)
            self.submit(path_to_tarball)
            
        except:
            raise
            
        else:
            self.log.info("'{}' submitted by {} at {}".format(
                self.assignment_name, self.student, self.timestamp))
            
        finally:
            shutil.rmtree(self.tmpdir)
