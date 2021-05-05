from . import NbGraderPreprocessor

from traitlets import Integer
from nbformat.notebooknode import NotebookNode
from nbconvert.exporters.exporter import ResourcesDict
from typing import Tuple


class RemoveExecutionInfo(NbGraderPreprocessor):
    """Preprocessor for removing execution info."""

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        if 'execution' in cell['metadata']:
            del cell['metadata']['execution']
        return cell, resources
