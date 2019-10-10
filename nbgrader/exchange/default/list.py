import os
import glob
import shutil
import re
import hashlib
from traitlets import Bool

from nbgrader.exchange.abc import ExchangeList as ABCExchangeList
from nbgrader.utils import notebook_hash, make_unique_key
from .exchange import Exchange


def _checksum(path):
    m = hashlib.md5()
    m.update(open(path, 'rb').read())
    return m.hexdigest()


class ExchangeList(Exchange, ABCExchangeList):

    def init_src(self):
        pass

    def init_dest(self):
        course_id = self.coursedir.course_id if self.coursedir.course_id else '*'
        assignment_id = self.coursedir.assignment_id if self.coursedir.assignment_id else '*'
        student_id = self.coursedir.student_id if self.coursedir.student_id else '*'

        if self.inbound:
            pattern = os.path.join(self.root, course_id, 'inbound', '{}+{}+*'.format(student_id, assignment_id))
        elif self.cached:
            pattern = os.path.join(self.cache, course_id, '{}+{}+*'.format(student_id, assignment_id))
        else:
            pattern = os.path.join(self.root, course_id, 'outbound', '{}'.format(assignment_id))

        self.assignments = sorted(glob.glob(pattern))

    def parse_assignment(self, assignment):
        if self.inbound:
            regexp = r".*/(?P<course_id>.*)/inbound/(?P<student_id>[^+]*)\+(?P<assignment_id>[^+]*)\+(?P<timestamp>[^+]*)(?P<random_string>\+.*)?"
        elif self.cached:
            regexp = r".*/(?P<course_id>.*)/(?P<student_id>.*)\+(?P<assignment_id>.*)\+(?P<timestamp>.*)"
        else:
            regexp = r".*/(?P<course_id>.*)/outbound/(?P<assignment_id>.*)"

        m = re.match(regexp, assignment)
        if m is None:
            raise RuntimeError("Could not match '%s' with regexp '%s'", assignment, regexp)
        return m.groupdict()

    def format_inbound_assignment(self, info):
        msg = "{course_id} {student_id} {assignment_id} {timestamp}".format(**info)
        if info['status'] == 'submitted':
            if info['has_local_feedback'] and not info['feedback_updated']:
                msg += " (feedback already fetched)"
            elif info['has_exchange_feedback']:
                msg += " (feedback ready to be fetched)"
            else:
                msg += " (no feedback available)"
        return msg

    def format_outbound_assignment(self, info):
        msg = "{course_id} {assignment_id}".format(**info)
        if os.path.exists(info['assignment_id']):
            msg += " (already downloaded)"
        return msg

    def copy_files(self):
        pass

    def parse_assignments(self):
        if self.coursedir.student_id:
            courses = self.authenticator.get_student_courses(self.coursedir.student_id)
        else:
            courses = None

        assignments = []
        for path in self.assignments:
            info = self.parse_assignment(path)
            if courses is not None and info['course_id'] not in courses:
                continue

            if self.path_includes_course:
                assignment_dir = os.path.join(self.assignment_dir, info['course_id'], info['assignment_id'])
            else:
                assignment_dir = os.path.join(self.assignment_dir, info['assignment_id'])

            if self.inbound or self.cached:
                info['status'] = 'submitted'
                info['path'] = path
            elif os.path.exists(assignment_dir):
                info['status'] = 'fetched'
                info['path'] = os.path.abspath(assignment_dir)
            else:
                info['status'] = 'released'
                info['path'] = path

            if self.remove:
                info['status'] = 'removed'

            notebooks = sorted(glob.glob(os.path.join(info['path'], '*.ipynb')))
            if not notebooks:
                self.log.warning("No notebooks found in {}".format(info['path']))

            info['notebooks'] = []
            for notebook in notebooks:
                nb_info = {
                    'notebook_id': os.path.splitext(os.path.split(notebook)[1])[0],
                    'path': os.path.abspath(notebook)
                }
                if info['status'] != 'submitted':
                    info['notebooks'].append(nb_info)
                    continue

                nb_info['has_local_feedback'] = False
                nb_info['has_exchange_feedback'] = False
                nb_info['local_feedback_path'] = None
                nb_info['feedback_updated'] = False

                # Check whether feedback has been fetched already.
                local_feedback_dir = os.path.join(
                    assignment_dir, 'feedback', info['timestamp'])
                local_feedback_path = os.path.join(
                    local_feedback_dir, '{0}.html'.format(nb_info['notebook_id']))
                has_local_feedback = os.path.isfile(local_feedback_path)
                if has_local_feedback:
                    local_feedback_checksum = _checksum(local_feedback_path)
                else:
                    local_feedback_checksum = None

                # Also look to see if there is feedback available to fetch.
                unique_key = make_unique_key(
                    info['course_id'],
                    info['assignment_id'],
                    nb_info['notebook_id'],
                    info['student_id'],
                    info['timestamp'])
                self.log.debug("Unique key is: {}".format(unique_key))
                nb_hash = notebook_hash(notebook, unique_key)
                exchange_feedback_path = os.path.join(
                    self.root, info['course_id'], 'feedback', '{0}.html'.format(nb_hash))
                has_exchange_feedback = os.path.isfile(exchange_feedback_path)
                if not has_exchange_feedback:
                    # Try looking for legacy feedback.
                    nb_hash = notebook_hash(notebook)
                    exchange_feedback_path = os.path.join(
                        self.root, info['course_id'], 'feedback', '{0}.html'.format(nb_hash))
                    has_exchange_feedback = os.path.isfile(exchange_feedback_path)
                if has_exchange_feedback:
                    exchange_feedback_checksum = _checksum(exchange_feedback_path)
                else:
                    exchange_feedback_checksum = None

                nb_info['has_local_feedback'] = has_local_feedback
                nb_info['has_exchange_feedback'] = has_exchange_feedback
                if has_local_feedback:
                    nb_info['local_feedback_path'] = local_feedback_path
                if has_local_feedback and has_exchange_feedback:
                    nb_info['feedback_updated'] = exchange_feedback_checksum != local_feedback_checksum
                info['notebooks'].append(nb_info)

            if info['status'] == 'submitted':
                if info['notebooks']:
                    has_local_feedback = all([nb['has_local_feedback'] for nb in info['notebooks']])
                    has_exchange_feedback = all([nb['has_exchange_feedback'] for nb in info['notebooks']])
                    feedback_updated = any([nb['feedback_updated'] for nb in info['notebooks']])
                else:
                    has_local_feedback = False
                    has_exchange_feedback = False
                    feedback_updated = False

                info['has_local_feedback'] = has_local_feedback
                info['has_exchange_feedback'] = has_exchange_feedback
                info['feedback_updated'] = feedback_updated
                if has_local_feedback:
                    info['local_feedback_path'] = os.path.join(
                        assignment_dir, 'feedback', info['timestamp'])
                else:
                    info['local_feedback_path'] = None

            assignments.append(info)

        # partition the assignments into groups for course/student/assignment
        if self.inbound or self.cached:
            _get_key = lambda info: (info['course_id'], info['student_id'], info['assignment_id'])
            _match_key = lambda info, key: (
                info['course_id'] == key[0] and
                info['student_id'] == key[1] and
                info['assignment_id'] == key[2])
            assignment_keys = sorted(list(set([_get_key(info) for info in assignments])))
            assignment_submissions = []
            for key in assignment_keys:
                submissions = [x for x in assignments if _match_key(x, key)]
                submissions = sorted(submissions, key=lambda x: x['timestamp'])
                info = {
                    'course_id': key[0],
                    'student_id': key[1],
                    'assignment_id': key[2],
                    'status': submissions[0]['status'],
                    'submissions': submissions
                }
                assignment_submissions.append(info)
            assignments = assignment_submissions

        return assignments

    def list_files(self):
        """List files."""
        assignments = self.parse_assignments()

        if self.inbound or self.cached:
            self.log.info("Submitted assignments:")
            for assignment in assignments:
                for info in assignment['submissions']:
                    self.log.info(self.format_inbound_assignment(info))
        else:
            self.log.info("Released assignments:")
            for info in assignments:
                self.log.info(self.format_outbound_assignment(info))

        return assignments

    def remove_files(self):
        """List and remove files."""
        assignments = self.parse_assignments()

        if self.inbound or self.cached:
            self.log.info("Removing submitted assignments:")
            for assignment in assignments:
                for info in assignment['submissions']:
                    self.log.info(self.format_inbound_assignment(info))
        else:
            self.log.info("Removing released assignments:")
            for info in assignments:
                self.log.info(self.format_outbound_assignment(info))

        for assignment in self.assignments:
            shutil.rmtree(assignment)

        return assignments

    def start(self):
        if self.inbound and self.cached:
            self.fail("Options --inbound and --cached are incompatible.")

        super(ExchangeList, self).start()

        if self.remove:
            return self.remove_files()
        else:
            return self.list_files()
