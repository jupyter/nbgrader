import os
import shutil
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISVTX, S_ISGID
)

from traitlets import Bool

from .baseapp import TransferApp, transfer_aliases, transfer_flags
from ..utils import self_owned


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
})

class ReleaseApp(TransferApp):

    name = u'nbgrader-release'
    description = u'Release an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Release an assignment to students. For the usage of instructors.

        This command is run from the top-level nbgrader folder. Before running
        this command, there are two things you must do.

        First, you have to set the unique `course_id` for the course. It must be
        unique for each instructor/course combination. To set it in the config
        file add a line to the `nbgrader_config.py` file:

            c.NbGrader.course_id = 'phys101'

        To pass the `course_id` at the command line, add `--course=phys101` to any
        of the below commands.

        Second, the assignment to be released must already be in the `release` folder.
        The usual way of getting an assignment into this folder is by running
        `nbgrader assign`.

        To release an assignment named `assignment1` run:

            nbgrader release assignment1

        If the assignment has already been released, you will have to add the
        `--force` flag to overwrite the released assignment:

            nbgrader release --force assignment1

        To query the exchange to see a list of your released assignments:

            nbgrader list
        """

    force = Bool(False, config=True, help="Force overwrite existing files in the exchange.")

    def build_extra_config(self):
        extra_config = super(ReleaseApp, self).build_extra_config()
        extra_config.NbGrader.student_id = '.'
        extra_config.NbGrader.notebook_id = '*'
        return extra_config

    def init_src(self):
        self.src_path = self._format_path(self.release_directory, self.student_id, self.assignment_id)
        if not os.path.isdir(self.src_path):
            source = self._format_path(self.source_directory, self.student_id, self.assignment_id)
            if os.path.isdir(source):
                # Looks like the instructor forgot to assign
                self.fail("Assignment found in '{}' but not '{}', run `nbgrader assign` first.".format(
                    source, self.src_path))
            else:
                self.fail("Assignment not found: {}".format(self.src_path))

    def init_dest(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        self.dest_path = os.path.join(self.outbound_path, self.assignment_id)
        # 0755
        self.ensure_directory(
            self.course_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        )
        # 0755
        self.ensure_directory(
            self.outbound_path,
            S_IRUSR|S_IWUSR|S_IXUSR|S_IRGRP|S_IXGRP|S_IROTH|S_IXOTH
        )
        # 0733 with set GID so student submission will have the instructors group
        self.ensure_directory(
            self.inbound_path,
            S_ISGID|S_IRUSR|S_IWUSR|S_IXUSR|S_IWGRP|S_IXGRP|S_IWOTH|S_IXOTH
        )

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
        if os.path.isdir(self.dest_path):
            if self.force:
                self.log.info("Overwriting files: {} {}".format(
                    self.course_id, self.assignment_id
                ))
                shutil.rmtree(self.dest_path)
            else:
                self.fail("Destination already exists, add --force to overwrite: {} {}".format(
                    self.course_id, self.assignment_id
                ))
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Released as: {} {}".format(self.course_id, self.assignment_id))
