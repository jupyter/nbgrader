from IPython.nbconvert.preprocessors import *
from IPython.utils.traitlets import Unicode

class GForm(Preprocessor):
    """A preprocessor for configuraing embedded Google Forms for grading."""

    form_id = Unicode(u'1vYvHgWVDrjGvxSJtJ_UhXcjczXaMYYUnjEVbF03ObOs', config=True)

    def preprocess(self, nb, resources):
        resources['nbgrader']['form_id'] = self.form_id
        return nb, resources
