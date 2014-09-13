from IPython.nbconvert.preprocessors import *
from IPython.utils.traitlets import Unicode

class GForm(Preprocessor):
    """A preprocessor for configuraing embedded Google Forms for grading."""

    student_id = Unicode(u'', config=True)
    grader_id = Unicode(u'', config=True)
    form_url = Unicode(u'', config=True)

    def preprocess(self, nb, resources):
        """
        Adds bold 'cheese' to the start of every markdown cell.
        """
        resources['nbgrader'] = {}
        resources['nbgrader']['student_id'] = self.student_id
        resources['nbgrader']['grader_id'] = self.grader_id
        resources['nbgrader']['form_url'] = self.form_url
        return nb, resources
