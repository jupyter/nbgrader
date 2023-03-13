from .. import utils
from . import NbGraderPreprocessor
from ..nbgraderformat import SCHEMA_REQUIRED
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Tuple


class DeduplicateIds(NbGraderPreprocessor):
    """A preprocessor to overwrite information about grade and solution cells."""

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        # keep track of grade ids encountered so far
        self.grade_ids = set([])

        # process each cell in reverse order
        nb, resources = super(DeduplicateIds, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int) -> Tuple[NotebookNode, ResourcesDict]:
        if not (utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell)):
            return cell, resources

        grade_id = cell.metadata.nbgrader['grade_id']
        if grade_id in self.grade_ids:
            self.log.warning("Cell with id '%s' exists multiple times!", grade_id)
            # Replace problematic metadata and leave message
            cell.source = "# THIS CELL CONTAINED A DUPLICATE ID DURING AUTOGRADING\n" + cell.source
            cell.metadata.nbgrader = SCHEMA_REQUIRED #| {"duplicate": True}  # doesn't work in python 3.8
            cell.metadata.nbgrader["duplicate"] = True
        else:
            self.grade_ids.add(grade_id)

        return cell, resources
