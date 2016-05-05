from textwrap import dedent
from traitlets import Unicode

from .base import BasePlugin


class LateSubmissionPlugin(BasePlugin):

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

    def late_submission_penalty(self, student_id, score, total_seconds_late):
        self.log.info("Using late submission penalty method: {}".format(self.penalty_method))
        if self.penalty_method == 'zero':
            return score
