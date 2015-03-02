import os
import re
from textwrap import dedent

from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode

class FindStudentID(Preprocessor):
    """Try to discover the student id given the full notebook path and a
    regular expression."""

    regexp = Unicode(
        r'', 
        config=True, 
        help=dedent(
            """
            The regular expression to use to find the student id based on the
            path and filename to the notebook. The regexp should include a named
            group for `student_id`, e.g. .*/(?P<student_id>.+)\.ipynb would 
            match files of the pattern <student_id>.ipynb
            """
        )
    )

    def preprocess(self, nb, resources):
        student_id = resources['nbgrader'].get('student', None)

        if not student_id and self.regexp == '':
            raise ValueError("No student id given, and the regexp is empty!")

        elif not student_id:
            path = resources['metadata'].get('path', '')
            name = resources['metadata'].get('name', '')
            if name == '':
                raise ValueError("invalid file name: {}".format(name))
            student_id = self.find_student_id(os.path.join(path, name + '.ipynb'))
            resources['nbgrader']['student'] = student_id

        self.log.info('Student ID: %s' % student_id)
        return nb, resources

    def find_student_id(self, filename):
        m = re.match(self.regexp, filename)
        if m is not None:
            gd = m.groupdict()
            if 'student_id' in gd:
                return gd['student_id']

        else:
            self.log.warn("No match found for regexp: {} (filename is: {})".format(
                self.regexp, filename))

        return ''
