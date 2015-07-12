import os

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags
from nbgrader.utils import check_mode


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
        Fetch an assignment that an instructor has released. For the usage of students.

        You can run this command from any directory, but usually, you will have a
        directory where you are keeping your course assignments.

        To fetch an assignment you must first know the `course_id` for your course.
        If you don't know it, ask your instructor.

        To show the list of assignments available for fetching (assume the `course_id`
        is `phys101`):

            nbgrader list phys101

        To fetch an assignment by name into the current directory:

            nbgrader fetch phys101 assignment1

        This will create an new directory named `assignment1` where you can work
        on the assignment. When you are done, use the `nbgrader submit` command
        to turn in the assignment.
        """

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
        if os.path.isdir(self.dest_path):
            self.fail("You already have a copy of the assignment in this directory: {}".format(self.assignment_id))

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Fetched as: {} {}".format(self.course_id, self.assignment_id))
