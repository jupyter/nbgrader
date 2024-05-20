from . import NbGraderPreprocessor

from traitlets import Unicode
from nbformat.notebooknode import NotebookNode
from nbconvert.exporters.exporter import ResourcesDict
from typing import Tuple
import re


class IgnorePattern(NbGraderPreprocessor):
    """Preprocessor for removing cell outputs that match a particular pattern"""
    
    pattern = Unicode("", help="The regular expression to remove from stderr").tag(config=True)
    
    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        
        if self.pattern and cell.cell_type == "code":
            new_outputs = []
            for output in cell.outputs:
                if output.output_type == "stream" and output.name == "stderr" \
                    and re.search(self.pattern, output.text):
                        continue
                new_outputs.append(output)
            cell.outputs = new_outputs
                    
        return cell, resources
