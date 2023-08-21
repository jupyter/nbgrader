from nbformat.v4.nbbase import validate

from .. import utils
from ..api import Gradebook, MissingEntry
from . import NbGraderPreprocessor
from ..nbgraderformat import MetadataValidator
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from traitlets import Bool, Unicode
from typing import Tuple, Any
from textwrap import dedent


class OverwriteCells(NbGraderPreprocessor):
    """A preprocessor to overwrite information about grade and solution cells."""

    add_missing_cells = Bool(
        False,
        help=dedent(
            """
            Whether or not missing grade_cells should be added back
            to the notebooks being graded.
            """
        ),
    ).tag(config=True)

    missing_cell_notification = Unicode(
        "This cell (id:{cell_id}) was missing from the submission. " +
        "It was added back by nbgrader.\n\n",  # Markdown requires two newlines
        help=dedent(
            """
            A text to add at the beginning of every missing cell re-added to the notebook during autograding.
            """
        )
    ).tag(config=True)

    def missing_cell_transform(self, source_cell, max_score, is_solution=False, is_task=False):
        """
        Converts source_cell obtained from Gradebook into a cell that can be added to the notebook.
        It is assumed that the cell is a grade_cell (unless is_task=True)
        """

        missing_cell_notification = self.missing_cell_notification.format(cell_id=source_cell.name)

        cell = {
            "cell_type": source_cell.cell_type,
            "metadata": {
                "deletable": False,
                "editable": False,
                "nbgrader": {
                    "grade": True,
                    "grade_id": source_cell.name,
                    "locked": source_cell.locked,
                    "checksum": source_cell.checksum,
                    "cell_type": source_cell.cell_type,
                    "points": max_score,
                    "solution": False
                }
            },
            "source": missing_cell_notification + source_cell.source
        }

        # Code cell format is slightly different
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
            cell["source"] = "# " + cell["source"]  # make the notification we add a comment

        # some grade cells are editable (manually graded answers)
        if is_solution:
            del cell["metadata"]["editable"]
            cell["metadata"]["nbgrader"]["solution"] = True
        # task cells are also a bit different
        elif is_task:
            cell["metadata"]["nbgrader"]["grade"] = False
            cell["metadata"]["nbgrader"]["task"] = True
            # this is when task cells were added so metadata validation should start from here
            cell["metadata"]["nbgrader"]["schema_version"] = 3

        cell = NotebookNode(cell)
        cell = MetadataValidator().upgrade_cell_metadata(cell)
        return cell

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.db_url = resources['nbgrader']['db_url']

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        with self.gradebook:
            nb, resources = super(OverwriteCells, self).preprocess(nb, resources)
            if self.add_missing_cells:
                nb, resources = self.add_missing_grade_cells(nb, resources)
                nb, resources = self.add_missing_task_cells(nb, resources)

        return nb, resources

    def add_missing_grade_cells(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        """
        Add missing grade cells back to the notebook.
        If missing, find the previous solution/grade cell, and add the current cell after it.
        It is assumed such a cell exists because
        presumably the grade_cell exists to grade some work in the solution cell.
        """
        source_nb = self.gradebook.find_notebook(self.notebook_id, self.assignment_id)
        source_cells = source_nb.source_cells
        source_cell_ids = [cell.name for cell in source_cells]
        grade_cells = {cell.name: cell for cell in source_nb.grade_cells}
        solution_cell_ids = [cell.name for cell in source_nb.solution_cells]

        # track indices of solution and grade cells in the submitted notebook
        submitted_cell_idxs = dict()
        for idx, cell in enumerate(nb.cells):
            if utils.is_grade(cell) or utils.is_solution(cell):
                submitted_cell_idxs[cell.metadata.nbgrader["grade_id"]] = idx

        # Every time we add a cell, the idxs above get shifted
        # We could process the notebook backwards, but that makes adding the cells in the right place more difficult
        # So we keep track of how many we have added so far
        added_count = 0

        for grade_cell_id, grade_cell in grade_cells.items():
            # If missing, find the previous solution/grade cell, and add the current cell after it.
            if grade_cell_id not in submitted_cell_idxs:
                self.log.warning(f"Missing grade cell {grade_cell_id} encountered, adding to notebook")
                source_cell_idx = source_cell_ids.index(grade_cell_id)
                cell_to_add = source_cells[source_cell_idx]
                cell_to_add = self.missing_cell_transform(cell_to_add, grade_cell.max_score,
                                                          is_solution=grade_cell_id in solution_cell_ids)
                # First cell was deleted, add it to start
                if source_cell_idx == 0:
                    nb.cells.insert(0, cell_to_add)
                    submitted_cell_idxs[grade_cell_id] = 0
                # Deleted cell is not the first, add it after the previous solution/grade cell
                else:
                    prev_cell_id = source_cell_ids[source_cell_idx - 1]
                    prev_cell_idx = submitted_cell_idxs[prev_cell_id] + added_count
                    nb.cells.insert(prev_cell_idx + 1, cell_to_add)  # +1 to add it after
                    submitted_cell_idxs[grade_cell_id] = submitted_cell_idxs[prev_cell_id]

                # If the cell we just added is followed by other missing cells, we need to know its index in the nb
                # However, no need to add `added_count` to avoid double-counting

                added_count += 1  # shift idxs

        return nb, resources

    def add_missing_task_cells(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        """
        Add missing task cells back to the notebook.
        We can't figure out their original location, so they are added at the end, in their original order.
        """
        source_nb = self.gradebook.find_notebook(self.notebook_id, self.assignment_id)
        source_cells = source_nb.source_cells
        source_cell_ids = [cell.name for cell in source_cells]
        submitted_ids = [cell["metadata"]["nbgrader"]["grade_id"] for cell in nb.cells if
                         "nbgrader" in cell["metadata"]]
        for task_cell in source_nb.task_cells:
            if task_cell.name not in submitted_ids:
                cell_to_add = source_cells[source_cell_ids.index(task_cell.name)]
                cell_to_add = self.missing_cell_transform(cell_to_add, task_cell.max_score, is_task=True)
                nb.cells.append(cell_to_add)

        return nb, resources

    def update_cell_type(self, cell: NotebookNode, cell_type: str) -> None:
        if cell.cell_type == cell_type:
            return
        elif cell_type == 'code':
            cell.cell_type = 'code'
            cell.outputs = []
            cell.execution_count = None
            validate(cell, 'code_cell')
        elif cell_type == 'markdown':
            cell.cell_type = 'markdown'
            if 'outputs' in cell:
                del cell['outputs']
            if 'execution_count' in cell:
                del cell['execution_count']
            validate(cell, 'markdown_cell')

    def report_change(self, name: str, attr: str, old: Any, new: Any) -> None:
        self.log.warning(
            "Attribute '%s' for cell %s has changed! (should be: %s, got: %s)", attr, name, old, new)

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        grade_id = cell.metadata.get('nbgrader', {}).get('grade_id', None)
        if grade_id is None:
            return cell, resources

        try:
            source_cell = self.gradebook.find_source_cell(
                grade_id,
                self.notebook_id,
                self.assignment_id)
        except MissingEntry:
            self.log.warning("Cell '{}' does not exist in the database".format(grade_id))
            del cell.metadata.nbgrader['grade_id']
            return cell, resources

        # check that the cell type hasn't changed
        if cell.cell_type != source_cell.cell_type:
            self.report_change(grade_id, "cell_type", source_cell.cell_type, cell.cell_type)
            self.update_cell_type(cell, source_cell.cell_type)

        # check that the locked status hasn't changed
        if utils.is_locked(cell) != source_cell.locked:
            self.report_change(grade_id, "locked", source_cell.locked, utils.is_locked(cell))
            cell.metadata.nbgrader["locked"] = source_cell.locked

        # if it's a grade cell, check that the max score hasn't changed
        if utils.is_grade(cell):
            grade_cell = self.gradebook.find_graded_cell(
                grade_id,
                self.notebook_id,
                self.assignment_id)
            old_points = float(grade_cell.max_score)
            new_points = float(cell.metadata.nbgrader["points"])

            if old_points != new_points:
                self.report_change(grade_id, "points", old_points, new_points)
                cell.metadata.nbgrader["points"] = old_points

        # always update the checksum, just in case
        cell.metadata.nbgrader["checksum"] = source_cell.checksum

        # if it's locked, check that the checksum hasn't changed
        if source_cell.locked:
            old_checksum = source_cell.checksum
            new_checksum = utils.compute_checksum(cell)
            if old_checksum != new_checksum:
                self.report_change(grade_id, "checksum", old_checksum, new_checksum)
                cell.source = source_cell.source
                # double check the the checksum is correct now
                if utils.compute_checksum(cell) != source_cell.checksum:
                    raise RuntimeError("Inconsistent checksums for cell {}".format(source_cell.name))

        return cell, resources
