import os
from stat import (
    S_IRUSR, S_IWUSR, S_IXUSR,
    S_IRGRP, S_IWGRP, S_IXGRP,
    S_IROTH, S_IWOTH, S_IXOTH,
    S_ISVTX, S_ISGID
)

from textwrap import dedent
from traitlets import Bool

from .baseapp import TransferApp, transfer_aliases, transfer_flags
from ..utils import get_username, check_mode, find_all_notebooks


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'strict': (
        {'SubmitApp': {'strict': True}},
        "Fail if the submission is missing notebooks for the assignment"
    ),
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

    strict = Bool(
        False,
        help=dedent(
            "Whether or not to submit the assignment if there are missing "
            "notebooks from the released assignment notebooks."
        )
    ).tag(config=True)

    def init_src(self):
        if self.path_includes_course:
            root = os.path.join(self.course_id, self.assignment_id)
        else:
            root = self.assignment_id
        self.src_path = os.path.abspath(root)
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

    def init_release(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        course_path = os.path.join(self.exchange_directory, self.course_id)
        outbound_path = os.path.join(course_path, 'outbound')
        self.release_path = os.path.join(outbound_path, self.assignment_id)
        if not os.path.isdir(self.release_path):
            self.fail("Assignment not found: {}".format(self.release_path))
        if not check_mode(self.release_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.release_path))

    def check_filename_diff(self):
        released_notebooks = find_all_notebooks(self.release_path)
        submitted_notebooks = find_all_notebooks(self.src_path)

        # Look for missing notebooks in submitted notebooks
        missing = False
        release_diff = list()
        for filename in released_notebooks:
            if filename in submitted_notebooks:
                release_diff.append("{}: {}".format(filename, 'FOUND'))
            else:
                missing = True
                release_diff.append("{}: {}".format(filename, 'MISSING'))

        # Look for extra notebooks in submitted notebooks
        extra = False
        submitted_diff = list()
        for filename in submitted_notebooks:
            if filename in released_notebooks:
                submitted_diff.append("{}: {}".format(filename, 'OK'))
            else:
                extra = True
                submitted_diff.append("{}: {}".format(filename, 'EXTRA'))

        if missing or extra:
            diff_msg = (
                "Expected:\n\t{}\nSubmitted:\n\t{}".format(
                    '\n\t'.join(release_diff),
                    '\n\t'.join(submitted_diff),
                )
            )
            if missing and self.strict:
                self.fail(
                    "Assignment {} not submitted. "
                    "There are missing notebooks for the submission:\n{}"
                    "".format(self.assignment_id, diff_msg)
                )
            else:
                self.log.warning(
                    "Possible missing notebooks and/or extra notebooks "
                    "submitted for assignment {}:\n{}"
                    "".format(self.assignment_id, diff_msg)
                )

    def copy_files(self):
        self.init_release()

        dest_path = os.path.join(self.inbound_path, self.assignment_filename)
        cache_path = os.path.join(self.cache_path, self.assignment_filename)

        self.log.info("Source: {}".format(self.src_path))
        self.log.info("Destination: {}".format(dest_path))

        # copy to the real location
        self.check_filename_diff()
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
