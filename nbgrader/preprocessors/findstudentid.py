import os
import re

from IPython.nbconvert.preprocessors import *
from IPython.utils.traitlets import Unicode

class FindStudentID(Preprocessor):
    """Try to discover the student id given the full notebook path and a regular expression."""

    regexp = Unicode(r'', config=True)

    def preprocess(self, nb, resources):
        student_id = resources['nbgrader']['student_id']
        if not student_id:
            path = resources['metadata']['path']
            name = resources['metadata']['name']
            filename = os.path.join(path, name+'.ipynb')
            student_id = self.find_student_id(filename)
            resources['nbgrader']['student_id'] = student_id
        self.log.info('Student ID: %s' % student_id)
        return nb, resources

    def find_student_id(self, filename):
        self.log.info('%r %r', filename, self.regexp)
        m = re.match(self.regexp, filename)
        if m is not None:
            gd = m.groupdict()
            if 'student_id' in gd:
                return gd['student_id']
        return ''

