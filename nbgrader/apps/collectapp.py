import os
import glob
import shutil
from collections import defaultdict
import dateutil
import dateutil.parser

from IPython.utils.traitlets import Unicode, List, Bool

from nbgrader.apps.baseapp import TransferApp, transfer_aliases, transfer_flags
from nbgrader.utils import check_mode


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
        Here we go...
        """
    
    update = Bool(
        False,
        config=True,
        help="Update existing submissions with ones that have newer timestamps."
    )
    
    def init_args(self):
        if len(self.extra_args) == 1:
            self.assignment_id = self.extra_args[0]
        else:
            self.fail("Invalid number of argument, call as `nbgrader release ASSIGNMENT`.")

    def _path_to_record(self, path):
        filename = os.path.split(path)[1]
        filename_list = filename.split('+')
        if len(filename_list) != 3:
            self.fail("Invalid filename: {}".format(filename))
        username = filename_list[0]
        timestamp = dateutil.parser.parse(filename_list[2])
        return {'username': username, 'filename': filename, 'timestamp': timestamp}
    
    def _sort_by_timestamp(self, records):
        return sorted(records, key=lambda item: item['timestamp'], reverse=True)
    
    def init_src(self):
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
        submit_dir = os.path.abspath(self.submitted_directory)
        if not os.path.isdir(submit_dir):
            os.mkdir(submit_dir)

    def _get_existing_timestamp(self, dest_path):
        """Get the timestamp, as a datetime object, of an existing submission."""
        timestamp_path = os.path.join(dest_path, 'timestamp.txt')
        if os.path.exists(timestamp_path):
            with open(timestamp_path, 'r') as fh:
                timestamp = fh.read().strip()
            return dateutil.parser.parse(timestamp)
        else:
            return None
            
    def copy_files(self):
        for rec in self.src_records:
            student_id = rec['username']
            src_path = os.path.join(self.inbound_path, rec['filename'])
            dest_path = os.path.abspath(self.directory_structure.format(
                nbgrader_step=self.submitted_directory,
                student_id=student_id,
                assignment_id=self.assignment_id
            ))
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
                    self.log.info("No newer submission to collect: {} {}".format(student_id, self.assignment_id))
                else:
                    self.log.info("Submission already exists, use --update to update: {} {}".format(student_id, self.assignment_id))
