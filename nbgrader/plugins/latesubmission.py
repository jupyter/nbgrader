from textwrap import dedent
from traitlets import Enum

from .base import BasePlugin
from typing import Optional


class LateSubmissionPlugin(BasePlugin):
    """Predefined methods for assigning penalties for late submission"""

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

    def late_submission_penalty(self, student_id: str, score: float, total_seconds_late: float) -> Optional[float]:
        """
        Return the late submission penalty based on the predefined method.

        Parameters
        ----------
        student_id:
            The unique id of the student
        score:
            The score the student obtained for the submitted notebook
        total_seconds_late:
            The total number of seconds the submitted notebook was late

        Returns
        -------
        penalty : float OR None
            The assigned penalty score (None for no assigned penalty)
        """
        self.log.info("Using late submission penalty method: {}".format(self.penalty_method))
        if self.penalty_method == 'zero':
            if total_seconds_late == 0:
                self.log.error("Assigning a penalty to a notebook that was not submitted late.")
            return score
