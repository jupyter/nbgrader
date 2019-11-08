import traceback

from ..nbgraderformat import MetadataValidator, ValidationError
from . import NbGraderPreprocessor
from nbformat.notebooknode import NotebookNode
from typing import Dict, Tuple

class CheckCellMetadata(NbGraderPreprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb: NotebookNode, resources: Dict) -> Tuple[NotebookNode, Dict]:
        try:
            MetadataValidator().validate_nb(nb)
        except ValidationError:
            self.log.error(traceback.format_exc())
            msg = "Notebook failed to validate; the nbgrader metadata may be corrupted."
            self.log.error(msg)
            raise ValidationError(msg)

        return nb, resources
