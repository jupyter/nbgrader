import os
import sys
import shutil

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
        "Only remove existing files in the exchange."
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

    remove = Bool(False, config=True, help="Only remove existing files in the exchange.")

    def init_args(self):
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]

    def init_src(self):
        self.src_path = os.path.abspath(os.path.join(self.release_directory, self.assignment_id))
        if not os.path.isdir(self.src_path):
            self.log.error("Assignment not found: {}/{}".format(self.release_directory, self.assignment_id))
            self.fail("You have to run `nbgrader release` from your main nbgrader directory.")
    
    def init_dest(self):
        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path, self.assignment_id)
        self.ensure_directory(self.course_path, 0o755)
        self.ensure_directory(self.outbound_path, 0o755)
        self.ensure_directory(self.inbound_path, 0o733)

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
            


