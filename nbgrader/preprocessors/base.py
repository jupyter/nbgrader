from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import List, Unicode, Bool

class NbGraderPreprocessor(Preprocessor):

    default_language = Unicode('ipython')
    display_data_priority = List(['text/html', 'application/pdf', 'text/latex', 'image/svg+xml', 'image/png', 'image/jpeg', 'text/plain'])
    enabled = Bool(True, config=True)
