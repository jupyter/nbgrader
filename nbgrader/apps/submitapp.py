import os
import shutil
import tempfile
import datetime
import tarfile
import glob
from dateutil.tz import gettz

from textwrap import dedent

from IPython.utils.traitlets import Unicode, List, Dict
from IPython.config.application import catch_config_error

from nbgrader.apps.baseapp import BaseApp, base_aliases, base_flags

aliases = {}
aliases.update(base_aliases)
aliases.update({
    "assignment": "SubmitApp.assignment_id",
    "submit-dir": "SubmitApp.submissions_directory",
    "timezone": "SubmitApp.timezone"
})

flags = {}
flags.update(base_flags)
flags.update({
})

class SubmitApp(BaseApp):

    name = Unicode(u'nbgrader-submit')
    description = Unicode(u'Submit a completed assignment')
    aliases = Dict(aliases)
    flags = Dict(flags)

    examples = Unicode(dedent(
        """
        To submit all files in the current directory under the name "ps01":
            nbgrader submit --assignment ps01

        To submit all files in the "Problem Set 1" directory under the name
        "Problem Set 1":
            nbgrader submit "Problem Set 1"

        To submit all files in the "Problem Set 1" directory under the name "ps01":
            nbgrader submit "Problem Set 1" --assignment ps01
        """
    ))

    student = Unicode(os.environ['USER'])

    timezone = Unicode(
        "UTC", config=True,
        help="Timezone for recording timestamps")

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z", config=True,
        help="Format string for timestamps")

    assignment_directory = Unicode(
        '.', config=True,
        help=dedent(
            """
            The directory containing the assignment to be submitted.
            """
        )
    )
    assignment_id = Unicode(
        '', config=True,
        help=dedent(
            """
            The name of the assignment. Defaults to the name of the assignment
            directory.
            """
        )
    )
    submissions_directory = Unicode(
        "{}/.nbgrader/submissions".format(os.environ['HOME']),
        config=True,
        help=dedent(
            """
            The directory where the submission will be saved.
            """
        )
    )

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__"
        ],
        config=True,
        help=dedent(
            """
            List of file names or file globs to be ignored when creating the
            submission.
            """
        )
    )

    @catch_config_error
    def initialize(self, argv=None):
        super(SubmitApp, self).initialize(argv)

        if not os.path.exists(self.submissions_directory):
            os.makedirs(self.submissions_directory)

        self.init_assignment_root()

        if self.assignment_id == '':
            self.assignment_id = os.path.basename(self.assignment_directory)

        # record the timestamp
        tz = gettz(self.timezone)
        if tz is None:
            raise ValueError("Invalid timezone: {}".format(self.timezone))
        self.timestamp = datetime.datetime.now(tz).strftime(self.timestamp_format)

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
        pth = os.path.join(self.tmpdir, self.assignment_id)
        shutil.copytree(self.assignment_directory, pth)
        os.chdir(self.tmpdir)

        # get the user name, write it to file
        with open(os.path.join(self.assignment_id, "user.txt"), "w") as fh:
            fh.write(self.student)

        # save the submission time
        with open(os.path.join(self.assignment_id, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        return pth

    def make_archive(self, path_to_submission):
        """Make a tarball of the submission. Returns the path to the created
        archive."""
        root, submission = os.path.split(path_to_submission)
        os.chdir(root)

        archive = os.path.join(self.tmpdir, "{}.tar.gz".format(self.assignment_id))
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
        archive = "{}.tar.gz".format(self.assignment_id)
        target = os.path.join(self.submissions_directory, archive)
        shutil.copy(path_to_tarball, target)
        self.log.debug("Saved to {}".format(target))
        return target

    def start(self):
        super(SubmitApp, self).start()
        self.tmpdir = tempfile.mkdtemp()
        self.assignment_directory = os.path.abspath(self.assignment_directory)
        self.submissions_directory = os.path.abspath(self.submissions_directory)

        try:
            path_to_copy = self.make_temp_copy()
            path_to_tarball = self.make_archive(path_to_copy)
            path_to_submission = self.submit(path_to_tarball)

        except:
            raise

        else:
            self.log.debug("Saved to '{}'".format(path_to_submission))
            print("'{}' submitted by {} at {}".format(
                self.assignment_id, self.student, self.timestamp))

        finally:
            shutil.rmtree(self.tmpdir)
