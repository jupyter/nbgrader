from traitlets import Instance
from traitlets import Type

from ..api import Gradebook, SubmittedNotebook
from ..plugins import BasePlugin
from ..plugins import LateSubmissionPlugin
from . import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Tuple


class AssignLatePenalties(NbGraderPreprocessor):
    """Preprocessor for assigning penalties for late submissions to the database"""

    plugin_class = Type(
        LateSubmissionPlugin,
        klass=BasePlugin,
        help="The plugin class for assigning the late penalty for each notebook."
    ).tag(config=True)

    plugin_inst = Instance(BasePlugin).tag(config=False)

    def init_plugin(self) -> None:
        self.plugin_inst = self.plugin_class(parent=self)

    def _check_late_penalty(self, notebook: SubmittedNotebook, penalty: float) -> float:
        msg = "(Penalty {}) Adjusting late submission penalty from {} to {}."
        if penalty < 0:
            self.log.warning(msg.format("< 0", penalty, 0))
            return 0

        assert notebook.score is not None
        if penalty > notebook.score:
            self.log.warning(msg.format("> score", penalty, notebook.score))
            return notebook.score

        return penalty

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        self.notebook_id = resources['nbgrader']['notebook']
        self.assignment_id = resources['nbgrader']['assignment']
        self.student_id = resources['nbgrader']['student']
        self.db_url = resources['nbgrader']['db_url']

        # init the plugin
        self.init_plugin()

        # connect to the database
        self.gradebook = Gradebook(self.db_url)

        with self.gradebook:
            # process the late submissions
            nb, resources = super(AssignLatePenalties, self).preprocess(nb, resources)
            assignment = self.gradebook.find_submission(
                self.assignment_id, self.student_id)
            notebook = self.gradebook.find_submission_notebook(
                self.notebook_id, self.assignment_id, self.student_id)

            # reset to None (zero)
            notebook.late_submission_penalty = None

            if assignment.total_seconds_late > 0:
                self.log.warning("{} is {} seconds late".format(
                    assignment, assignment.total_seconds_late))

                late_penalty = self.plugin_inst.late_submission_penalty(
                    self.student_id, notebook.score, assignment.total_seconds_late)
                self.log.warning("Late submission penalty: {}".format(late_penalty))

                if late_penalty is not None:
                    late_penalty = self._check_late_penalty(notebook, late_penalty)
                    notebook.late_submission_penalty = late_penalty

            self.gradebook.db.commit()

        return nb, resources

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        return cell, resources
