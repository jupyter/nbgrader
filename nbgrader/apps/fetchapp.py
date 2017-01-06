import os
import shutil

from textwrap import dedent
from traitlets import Bool

from .baseapp import TransferApp, transfer_aliases, transfer_flags
from ..utils import check_mode


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'replace': (
        {'FetchApp' : {'replace_missing_files' : True}},
        "replace missing files, even if the assignment has already been fetched"
    ),
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

        To fetch an assignment by name into the current directory:

            nbgrader fetch assignment1

        To fetch an assignment for a specific course, you must first know the
        `course_id` for your course.  If you don't know it, ask your instructor.
        Then, simply include the argument with the '--course' flag.

            nbgrader fetch assignment1 --course=phys101

        This will create an new directory named `assignment1` where you can work
        on the assignment. When you are done, use the `nbgrader submit` command
        to turn in the assignment.
        """

    replace_missing_files = Bool(False, help="Whether to replace missing files on fetch").tag(config=True)

    def init_src(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.outbound_path = os.path.join(self.course_path, 'outbound')
        self.src_path = os.path.join(self.outbound_path, self.assignment_id)
        if not os.path.isdir(self.src_path):
            self.fail("Assignment not found: {}".format(self.src_path))
        if not check_mode(self.src_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.src_path))

    def init_dest(self):
        if self.path_includes_course:
            root = os.path.join(self.course_id, self.assignment_id)
        else:
            root = self.assignment_id
        self.dest_path = os.path.abspath(os.path.join('.', root))
        if os.path.isdir(self.dest_path) and not self.replace_missing_files:
            self.fail("You already have a copy of the assignment in this directory: {}".format(root))

    def copy_if_missing(self, src, dest, ignore=None):
        filenames = sorted(os.listdir(src))
        if ignore:
            bad_filenames = ignore(src, filenames)
            filenames = sorted(list(set(filenames) - bad_filenames))

        for filename in filenames:
            srcpath = os.path.join(src, filename)
            destpath = os.path.join(dest, filename)
            relpath = os.path.relpath(destpath, os.getcwd())
            if not os.path.exists(destpath):
                if os.path.isdir(srcpath):
                    self.log.warn("Creating missing directory '%s'", relpath)
                    os.mkdir(destpath)

                else:
                    self.log.warn("Replacing missing file '%s'", relpath)
                    shutil.copy(srcpath, destpath)

            if os.path.isdir(srcpath):
                self.copy_if_missing(srcpath, destpath, ignore=ignore)


    def do_copy(self, src, dest, perms=None):
        """Copy the src dir to the dest dir omitting the self.ignore globs."""
        if os.path.isdir(self.dest_path):
            self.copy_if_missing(src, dest, ignore=shutil.ignore_patterns(*self.ignore))
        else:
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns(*self.ignore))

        if perms:
            for dirname, dirnames, filenames in os.walk(dest):
                for filename in filenames:
                    os.chmod(os.path.join(dirname, filename), perms)

    def copy_files(self):
        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(self.dest_path))
        self.do_copy(self.src_path, self.dest_path)
        self.log.info("Fetched as: {} {}".format(self.course_id, self.assignment_id))
