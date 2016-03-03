import os
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISVTX, S_ISGID
)

from .baseapp import TransferApp, transfer_aliases, transfer_flags
from ..utils import get_username, check_mode


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
})

class SubmitApp(TransferApp):

    name = u'nbgrader-submit'
    description = u'Submit an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Submit an assignment for grading. For the usage of students.

        You must run this command from the directory containing the assignments
        sub-directory. For example, if you want to submit an assignment named
        `assignment1`, that must be a sub-directory of your current working directory.
        If you are inside the `assignment1` directory, it won't work.

        To fetch an assignment you must first know the `course_id` for your course.
        If you don't know it, ask your instructor.

        To submit `assignment1` to the course `phys101`:

            nbgrader submit assignment1 --course phys101

        You can submit an assignment multiple times and the instructor will always
        get the most recent version. Your assignment submission are timestamped
        so instructors can tell when you turned it in. No other students will
        be able to see your submissions.
        """

    def init_src(self):
        self.src_path = os.path.abspath(self.assignment_id)
        self.assignment_id = os.path.split(self.src_path)[-1]
        if not os.path.isdir(self.src_path):
            self.fail("Assignment not found: {}".format(self.src_path))

    def init_dest(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.inbound_path = os.path.join(self.exchange_directory, self.course_id, 'inbound')
        if not os.path.isdir(self.inbound_path):
            self.fail("Inbound directory doesn't exist: {}".format(self.inbound_path))
        if not check_mode(self.inbound_path, write=True, execute=True):
            self.fail("You don't have write permissions to the directory: {}".format(self.inbound_path))

        self.cache_path = os.path.join(self.cache_directory, self.course_id)
        self.assignment_filename = '{}+{}+{}'.format(get_username(), self.assignment_id, self.timestamp)

    def copy_files(self):
        dest_path = os.path.join(self.inbound_path, self.assignment_filename)
        cache_path = os.path.join(self.cache_path, self.assignment_filename)

        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(dest_path))

        # copy to the real location
        self.do_copy(self.src_path, dest_path, perms=(S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH))
        with open(os.path.join(dest_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        # Make this 0777=ugo=rwx so the instructor can delete later. Hidden from other users by the timestamp.
        os.chmod(
            dest_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IWGRP|S_IXGRP|S_IROTH|S_IWOTH|S_IXOTH
        )

        # also copy to the cache
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        self.do_copy(self.src_path, cache_path)
        with open(os.path.join(cache_path, "timestamp.txt"), "w") as fh:
            fh.write(self.timestamp)

        self.log.info("Submitted as: {} {} {}".format(
            self.course_id, self.assignment_id, str(self.timestamp)
        ))
