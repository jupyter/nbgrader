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

def _load_jupyter_server_extension(app):
    load_assignments(app)
    load_courses(app)
    load_formgrader(app)
    load_validate(app)
