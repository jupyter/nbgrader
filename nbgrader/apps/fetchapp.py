import os

from IPython.utils.traitlets import Unicode, List, Bool

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags
from nbgrader.utils import get_username, check_mode


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
})

class FetchApp(TransferApp):

    name = u'nbgrader-fetch'
    description = u'Fetch an assignment from the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Here we go...
        """
    
    def init_args(self):
        if len(self.extra_args) == 2:
            self.course_id = self.extra_args[0]
            self.assignment_id = self.extra_args[1]
        else:
            self.fail("Invalid number of args, call as `nbgrader fetch course_id assignment_id`")

    def init_src(self):
        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.src_path = os.path.join(self.outbound_path, self.assignment_id)
        if not os.path.isdir(self.src_path):
            self.fail("Assignment not found: {}".format(self.src_path))
        if not check_mode(self.src_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.src_path))
    
    def init_dest(self):
        self.dest_path = os.path.abspath(os.path.join('.', self.assignment_id))

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Fetched as: {} {}".format(self.course_id, self.assignment_id))
