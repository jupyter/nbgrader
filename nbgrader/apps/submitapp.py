import os

from IPython.utils.traitlets import Unicode, List, Bool

from nbgrader.apps.baseapp import TransferApp, nbgrader_aliases, nbgrader_flags
from nbgrader.utils import get_username, check_mode

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "SubmitApp.timezone"
})

flags = {}
flags.update(nbgrader_flags)


class SubmitApp(TransferApp):

    name = u'nbgrader-submit'
    description = u'Submit an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Here we go...
        """
    
    def init_args(self):
        if len(self.extra_args) == 2:
            # The first argument (assignment_id) is processed in init_src
            self.course_id = self.extra_args[1]
        else:
            self.fail("Invalide number of args, call as `nbgrader submit course_id assignment_id`")

    def init_src(self):
        self.src_path = os.path.abspath(self.extra_args[0])
        self.assignment_id = os.path.split(self.src_path)[-1]
        if not os.path.isdir(self.src_path):
            self.fail("Assignment not found: {}".format(self.src_path))
    
    def init_dest(self):
        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.assignment_filename = get_username() + '-' + self.assignment_id + '-' + self.timestamp
        self.dest_path = os.path.join(self.inbound_path, self.assignment_filename)
    
    def ensure_directories(self):
        """Ensure the dest directories exist and have the right mode/owner."""
        if not os.path.isdir(self.inbound_path):
            self.fail("Inbound directory doesn't exist: {}".format(self.inbound_path))
        if not check_mode(self.inbound_path, write=True, execute=True):
            self.fail("You don't have write permissions to the directory: {}".format(self.inbound_path))

    def copy_files(self):
        self.do_copy(self.src_path, self.dest_path)
        with open(os.path.join(self.dest_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.log.info("Submitted as: {} {}".format(self.course_id, self.assignment_filename))
