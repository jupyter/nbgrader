from textwrap import dedent
from traitlets import List
from traitlets import Unicode
from traitlets import validate

from .base import BasePluginLoader


class LateSubmissionPlugin(BasePluginLoader):

    supported_methods = List(['none', 'zero', 'custom'])

    penalty_method = Unicode(
        'none',
        help=dedent(
            """
            The method for assigning late submission penalties.
            Predefined methods:
                'none':
                'zero':
            """
        ),
    ).tag(config=True)

    def late_submission_penalty(self, assignment, notebook):
        self.log.info("Using late submission penalty method: {}".format(self.penalty_method))
        if self.penalty_method == 'zero':
            return assignment.score

        if self.penalty_method == 'custom':
            plugin = self.import_plugin()
            fname = self.plugin_file_name
            if plugin is None:
                self.log.warning(
                    ' '.join(["plugin file '{}.py' not found.".format(fname),
                              "No late submission penalty assigned."])
                )

            else:
                penalty = plugin.late_submission_penalty(
                    assignment.student_id,
                    notebook.score,
                    assignment.total_seconds_late
                )
                return min(assignment.score, abs(penalty))
