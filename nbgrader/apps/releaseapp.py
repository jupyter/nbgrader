import os
import sys
import shutil
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISVTX, S_ISGID
)

from IPython.utils.traitlets import Unicode, List, Bool

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags
from nbgrader.utils import self_owned


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'force': (
        {'ReleaseApp' : {'force' : True}},
        "Force overwrite of existing files in the exchange."
    ),
    'remove': (
        {'ReleaseApp' : {'remove': True}},
        "Unrelease an assignment by removing it from the exchange."
    ),
})

class ReleaseApp(TransferApp):

    name = u'nbgrader-release'
    description = u'Release an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Here we go...
        """

    force = Bool(False, config=True, help="Force overwrite existing files in the exchange.")

    remove = Bool(False, config=True, help="Unrelease an assignment by removing it from the exchange.")

    def init_args(self):
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
        else:
            self.fail("Invalid number of argument, call as `nbgrader release ASSIGNMENT`.")

    def init_src(self):
        self.src_path = os.path.abspath(os.path.join(self.release_directory, self.assignment_id))
        if not os.path.isdir(self.src_path):
            self.log.error("Assignment not found: {}/{}".format(self.release_directory, self.assignment_id))
            if os.path.isdir(os.path.join(self.source_directory, self.assignment_id)):
                # Looks like the instructor forgot to assign
                self.fail("Assignment found in ./{} but not ./{}, run `nbgrader assign` first.".format(
                    self.source_directory, self.release_directory
                )) 
            else:
                self.fail("You have to run `nbgrader release {}` from your main nbgrader directory.".format(self.assignment_id))
    
    def init_dest(self):
        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path, self.assignment_id)
        # 0755
        self.ensure_directory(self.course_path, S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH)
        # 0755
        self.ensure_directory(self.outbound_path, S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH)
        # 0733 with set GID so student submission will have the instructors group
        self.ensure_directory(self.inbound_path, S_ISGID|S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IWOTH|S_IXOTH)

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
        if self.remove:
            if os.path.isdir(self.dest_path):
                self.log.info("Removing old files: {} {}".format(self.course_id, self.assignment_id))
                shutil.rmtree(self.dest_path)
            else:
                self.log.info("No existing files exist for: {} {}".format(self.course_id, self.assignment_id))
        else:
            if os.path.isdir(self.dest_path):
                if self.force:
                    self.log.info("Overwriting files: {} {}".format(self.course_id, self.assignment_id))
                    shutil.rmtree(self.dest_path)
                else:
                    self.fail("Destination already exists, add --force to overwrite: {} {}".format(self.course_id, self.assignment_id))
            self.log.info("Source: {}".format(self.src_path))
            self.log.info("Destination: {}".format(self.dest_path))
            self.do_copy(self.src_path, self.dest_path)
            self.log.info("Released as: {} {}".format(self.course_id, self.assignment_id))
            


