"""
A system for assigning and grading notebooks.
"""

import os
import sys
import json
from pathlib import Path
from ._version import __version__

from .server_extensions.assignment_list import load_jupyter_server_extension as load_assignments
from .server_extensions.course_list import load_jupyter_server_extension as load_courses
from .server_extensions.validate_assignment import load_jupyter_server_extension as load_validate
from .server_extensions.formgrader import load_jupyter_server_extension as load_formgrader

HERE = Path(__file__).parent.resolve()


if os.path.exists(HERE / "labextension"):
    with (HERE / "labextension" / "package.json").open() as fid:
        data = json.load(fid)


    def _jupyter_labextension_paths():
        return [{
            "src": "labextension",
            "dest": data["name"]
        }]


def _jupyter_server_extension_points():
    return [{
        "module": "nbgrader"
    }]


# Classic notebook extensions
def _jupyter_nbextension_paths():
    paths = [
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
        )
    ]

    if sys.platform != 'win32':
        paths.append(
            dict(
                section="tree",
                src=os.path.join('nbextensions', 'assignment_list'),
                dest="assignment_list",
                require="assignment_list/main"
            )
        )
        paths.append(
            dict(
                section="tree",
                src=os.path.join('nbextensions', 'course_list'),
                dest="course_list",
                require="course_list/main"
            )
        )

    return paths


# Classic notebook server extensions
def _jupyter_server_extension_paths():
    paths = [
        dict(module="nbgrader.server_extensions.formgrader"),
        dict(module="nbgrader.server_extensions.validate_assignment")
    ]

    if sys.platform != 'win32':
        paths.append(dict(module="nbgrader.server_extensions.assignment_list"))
        paths.append(dict(module="nbgrader.server_extensions.course_list"))

    return paths


def _load_jupyter_server_extension(app):
    load_assignments(app)
    load_courses(app)
    load_formgrader(app)
    load_validate(app)
