from ..nbformat import Validator
from . import NbGraderPreprocessor

class CheckCellMetadata(NbGraderPreprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb, resources):
        Validator().validate_nb(nb)
        return nb, resources
