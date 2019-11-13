from .. import utils
from . import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Tuple

class ComputeChecksums(NbGraderPreprocessor):
    """A preprocessor to compute checksums of grade cells."""

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        # compute checksums of grade cell and solution cells
        if utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell):
            checksum = utils.compute_checksum(cell)
            cell.metadata.nbgrader['checksum'] = checksum
            cell.metadata.nbgrader['cell_type'] = cell.cell_type

            if utils.is_grade(cell) or utils.is_solution(cell):
                self.log.debug(
                    "Checksum for %s cell '%s' is %s",
                    cell.metadata.nbgrader['cell_type'],
                    cell.metadata.nbgrader['grade_id'],
                    checksum)

        return cell, resources
