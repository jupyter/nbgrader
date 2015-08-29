import os
import glob
import shutil
from collections import defaultdict

from traitlets import Bool

from .baseapp import TransferApp, transfer_aliases, transfer_flags
from ..utils import check_mode, parse_utc


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'update': (
        {'CollectApp' : {'update': True}},
        "Update existing submissions with ones that have newer timestamps."
    ),
})

def groupby(l, key=lambda x: x):
    d = defaultdict(list)
    for item in l:
        d[key(item)].append(item)
    return d

class CollectApp(TransferApp):

    name = u'nbgrader-collect'
    description = u'Collect an assignment from the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Collect assignments students have submitted. For the usage of instructors.

        This command is run from the top-level nbgrader folder. Before running
        this command, you may want toset the unique `course_id` for the course.
        It must be unique for each instructor/course combination. To set it in
        the config file add a line to the `nbgrader_config.py` file:

            c.NbGrader.course_id = 'phys101'

        To pass the `course_id` at the command line, add `--course=phys101` to any
        of the below commands.

        To collect `assignment1` for all students:

            nbgrader collect assignment1

        To collect `assignment1` for only `student1`:

            nbgrader collect --student=student1 assignment1

        Collected assignments will go into the `submitted` folder with the proper
        directory structure to start grading. All submissions are timestamped and
        students can turn an assignment in multiple times. The `collect` command
        will always get the most recent submission from each student, but it will
        never overwrite an existing submission unless you provide the `--update`
        flag:

            nbgrader collect --update assignment1
        """

    update = Bool(
        False,
        config=True,
        help="Update existing submissions with ones that have newer timestamps."
    )

    def _path_to_record(self, path):
        filename = os.path.split(path)[1]
        # Only split twice on +, giving three components. This allows usernames with +.
        filename_list = filename.rsplit('+', 2)
        if len(filename_list) != 3:
            self.fail("Invalid filename: {}".format(filename))
        username = filename_list[0]
        timestamp = parse_utc(filename_list[2])
        return {'username': username, 'filename': filename, 'timestamp': timestamp}

    def _sort_by_timestamp(self, records):
        return sorted(records, key=lambda item: item['timestamp'], reverse=True)

    def init_src(self):
        if self.course_id == '':
            self.fail("No course id specified. Re-run with --course flag.")

        self.course_path = os.path.join(self.exchange_directory, self.course_id)
        self.inbound_path = os.path.join(self.course_path, 'inbound')
        if not os.path.isdir(self.inbound_path):
            self.fail("Course not found: {}".format(self.inbound_path))
        if not check_mode(self.inbound_path, read=True, execute=True):
            self.fail("You don't have read permissions for the directory: {}".format(self.inbound_path))
        student_id = self.student_id if self.student_id else '*'
        pattern = os.path.join(self.inbound_path, '{}+{}+*'.format(student_id, self.assignment_id))
        records = [self._path_to_record(f) for f in glob.glob(pattern)]
        usergroups = groupby(records, lambda item: item['username'])
        self.src_records = [self._sort_by_timestamp(v)[0] for v in usergroups.values()]

    def init_dest(self):
        pass

    def copy_files(self):
        for rec in self.src_records:
            student_id = rec['username']
            src_path = os.path.join(self.inbound_path, rec['filename'])
            dest_path = self._format_path(self.submitted_directory, student_id, self.assignment_id)
            if not os.path.exists(os.path.dirname(dest_path)):
                os.makedirs(os.path.dirname(dest_path))

            copy = False
            updating = False
            if os.path.isdir(dest_path):
                existing_timestamp = self._get_existing_timestamp(dest_path)
                new_timestamp = rec['timestamp']
                if self.update and (existing_timestamp is None or new_timestamp > existing_timestamp):
                    copy = True
                    updating = True
            else:
                copy = True

            if copy:
                if updating:
                    self.log.info("Updating submission: {} {}".format(student_id, self.assignment_id))
                    shutil.rmtree(dest_path)
                else:
                    self.log.info("Collecting submission: {} {}".format(student_id, self.assignment_id))
                self.do_copy(src_path, dest_path)
            else:
                if self.update:
                    self.log.info("No newer submission to collect: {} {}".format(
                        student_id, self.assignment_id
                    ))
                else:
                    self.log.info("Submission already exists, use --update to update: {} {}".format(
                        student_id, self.assignment_id
                    ))
