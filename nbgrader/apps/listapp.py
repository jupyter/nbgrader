import os
import glob
import shutil
import re
import json

from traitlets import Bool

from .baseapp import TransferApp, transfer_aliases, transfer_flags


aliases = {}
aliases.update(transfer_aliases)
aliases.update({
})

flags = {}
flags.update(transfer_flags)
flags.update({
    'inbound': (
        {'ListApp' : {'inbound': True}},
        "List inbound files rather than outbound."
    ),
    'cached': (
        {'ListApp' : {'cached': True}},
        "List cached files rather than inbound/outbound."
    ),
    'remove': (
        {'ListApp' : {'remove': True}},
        "Remove an assignment from the exchange."
    ),
    'json': (
        {'ListApp' : {'as_json': True}},
        "Print out assignments as json."
    ),
})

class ListApp(TransferApp):

    name = u'nbgrader-list'
    description = u'List assignments in the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        List assignments in the nbgrader exchange. For the usage of instructors
        and students.

        Students
        ========

        To list assignments for a course, you must first know the `course_id` for
        your course. If you don't know it, ask your instructor.

        To list the released assignments for the course `phys101`:

            nbgrader list phys101

        Instructors
        ===========

        To list outbound (released) or inbound (submitted) assignments for a course,
        you must configure the `course_id` in your config file or the command line.

        To see all of the released assignments, run

            nbgrader list  # course_id in the config file

        or

            nbgrader list --course phys101  # course_id provided

        To see the inbound (submitted) assignments:

            nbgrader list --inbound

        You can use the `--student` and `--assignment` options to filter the list
        by student or assignment:

            nbgrader list --inbound --student=student1 --assignment=assignment1

        If a student has submitted an assignment multiple times, the `list` command
        will show all submissions with their timestamps.

        The `list` command can optionally remove listed assignments by providing the
        `--remove` flag:

            nbgrader list --inbound --remove --student=student1
        """

    inbound = Bool(False, help="List inbound files rather than outbound.").tag(config=True)
    cached = Bool(False, help="List assignments in submission cache.").tag(config=True)
    remove = Bool(False, help="Remove, rather than list files.").tag(config=True)
    as_json = Bool(False, help="Print out assignments as json").tag(config=True)

    def init_src(self):
        pass

    def init_dest(self):
        course_id = self.course_id if self.course_id else '*'
        assignment_id = self.assignment_id if self.assignment_id else '*'
        student_id = self.student_id if self.student_id else '*'

        if self.inbound:
            pattern = os.path.join(self.exchange_directory, course_id, 'inbound', '{}+{}+*'.format(student_id, assignment_id))
        elif self.cached:
            pattern = os.path.join(self.cache_directory, course_id, '{}+{}+*'.format(student_id, assignment_id))
        else:
            pattern = os.path.join(self.exchange_directory, course_id, 'outbound', '{}'.format(assignment_id))

        self.assignments = sorted(glob.glob(pattern))

    def parse_assignment(self, assignment):
        if self.inbound:
            regexp = r".*/(?P<course_id>.*)/inbound/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        elif self.cached:
            regexp = r".*/(?P<course_id>.*)/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        else:
            regexp = r".*/(?P<course_id>.*)/outbound/(?P<assignment_id>.*)"

        m = re.match(regexp, assignment)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
        return m.groupdict()

    def format_inbound_assignment(self, info):
        return "{course_id} {student_id} {assignment_id} {timestamp}".format(**info)

    def format_outbound_assignment(self, info):
        msg = "{course_id} {assignment_id}".format(**info)
        if os.path.exists(info['assignment_id']):
            msg += " (already downloaded)"
        return msg

    def copy_files(self):
        pass

    def parse_assignments(self):
        assignments = []
        for path in self.assignments:
            info = self.parse_assignment(path)
            if self.path_includes_course:
                root = os.path.join(info['course_id'], info['assignment_id'])
            else:
                root = info['assignment_id']

            if self.inbound or self.cached:
                info['status'] = 'submitted'
                info['path'] = path
            elif os.path.exists(root):
                info['status'] = 'fetched'
                info['path'] = os.path.abspath(root)
            else:
                info['status'] = 'released'
                info['path'] = path

            if self.remove:
                info['status'] = 'removed'

            info['notebooks'] = []
            for notebook in sorted(glob.glob(os.path.join(info['path'], '*.ipynb'))):
                info['notebooks'].append({
                    'notebook_id': os.path.splitext(os.path.split(notebook)[1])[0],
                    'path': os.path.abspath(notebook)
                })

            assignments.append(info)

        return assignments

    def list_files(self):
        """List files."""
        assignments = self.parse_assignments()

        if self.as_json:
            print(json.dumps(assignments))

        else:
            if self.inbound or self.cached:
                self.log.info("Submitted assignments:")
                for info in assignments:
                    self.log.info(self.format_inbound_assignment(info))
            else:
                self.log.info("Released assignments:")
                for info in assignments:
                    self.log.info(self.format_outbound_assignment(info))

    def remove_files(self):
        """List and remove files."""
        assignments = self.parse_assignments()

        if self.as_json:
            print(json.dumps(assignments))

        else:
            if self.inbound or self.cached:
                self.log.info("Removing submitted assignments:")
                for info in assignments:
                    self.log.info(self.format_inbound_assignment(info))
            else:
                self.log.info("Removing released assignments:")
                for info in assignments:
                    self.log.info(self.format_outbound_assignment(info))

        for assignment in self.assignments:
            shutil.rmtree(assignment)

    def start(self):
        if self.inbound and self.cached:
            self.fail("Options --inbound and --cached are incompatible.")

        if len(self.extra_args) == 0:
            self.extra_args = ["*"] # allow user to not put in assignment

        super(ListApp, self).start()

        if self.remove:
            self.remove_files()
        else:
            self.list_files()
