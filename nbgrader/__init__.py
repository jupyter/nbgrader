"""
A system for assigning and grading notebooks.
"""

import os
from ._version import version_info, __version__


def _jupyter_nbextension_paths():
    return [
        dict(
            section="tree",
            src=os.path.join('nbextensions', 'assignment_list'),
            dest="assignment_list",
            require="assignment_list/main"
        ),
        dict(
            section="notebook",
            src=os.path.join('nbextensions', 'create_assignment'),
            dest="create_assignment",
            require="create_assignment/main"
        ),
        dict(
            section="tree",
            src=os.path.join('nbextensions', 'formgrader'),
            dest="formgrader",
            require="formgrader/main"
        ),
        dict(
            section="notebook",
            src=os.path.join('nbextensions', 'validate_assignment'),
            dest="validate_assignment",
            require="validate_assignment/main"
        ),
    ]

def _jupyter_server_extension_paths():
    return [
        dict(module="nbgrader.server_extensions.assignment_list"),
        dict(module="nbgrader.server_extensions.formgrader"),
        dict(module="nbgrader.server_extensions.validate_assignment")
    ]
