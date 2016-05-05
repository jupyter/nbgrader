from textwrap import dedent
from traitlets import Enum

from .base import BasePlugin


class LateSubmissionPlugin(BasePlugin):
    """Predifined methods for assigning penalties for late submission"""

    penalty_method = Enum(
        ('none', 'zero'),
        default_value='none',
        help=dedent(
            """
            The method for assigning late submission penalties:
                'none': do nothing (no penalty assigned)
                'zero': assign an overall score of zero (penalty = score)
            """
        ),
    ).tag(config=True)

    def late_submission_penalty(self, student_id, score, total_seconds_late):
        self.log.info("Using late submission penalty method: {}".format(self.penalty_method))
        if self.penalty_method == 'zero':
            if total_seconds_late == 0:
                self.log.error("Assigning a penalty to a notebook that was not submitted late.")
            return score
