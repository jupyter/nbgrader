from IPython.config import Configurable
from IPython.utils.traitlets import Unicode

from textwrap import dedent

class NbGraderConfig(Configurable):
    db_url = Unicode("sqlite:///gradebook.db", config=True, help="URL to the database")

    student_id = Unicode(
        "*",
        config=True,
        help=dedent(
            """
            File glob to match student ids. This can be changed to filter by 
            student id.
            """
        )
    )

    assignment_id = Unicode(
        "",
        config=True,
        help=dedent(
            """
            File glob to match assignment names. This can be changed to filter 
            by assignment id.
            """
        )
    )

    notebook_id = Unicode(
        "*",
        config=True,
        help=dedent(
            """
            File glob to match notebook ids, excluding the '.ipynb' extension. 
            This can be changed to filter by notebook id.
            """
        )
    )

    directory_structure = Unicode(
        "{nbgrader_step}/{student_id}/{assignment_id}",
        config=True,
        help=dedent(
            """
            Format string for the directory structure that nbgrader works 
            over during the grading process. This MUST contain named keys for 
            'nbgrader_step', 'student_id', and 'assignment_id'.
            """
        )
    )
