import os
import re
from textwrap import dedent

from traitlets import List, Bool, default

from ..api import Gradebook, MissingEntry
from .base import BaseConverter, NbGraderException
from ..preprocessors import (
    IncludeHeaderFooter,
    LockCells,
    SaveCells,
    ClearOutput,
    ClearMarkScheme,
    Execute,
)
from traitlets.config.loader import Config
from typing import Any
from ..coursedir import CourseDirectory


class GenerateSolution(BaseConverter):

    create_assignment = Bool(
        True,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        )
    ).tag(config=True)

    @default("permissions")
    def _permissions_default(self) -> int:
        return 664 if self.coursedir.groupshared else 644

    @property
    def _input_directory(self) -> str:
        return self.coursedir.source_directory

    @property
    def _output_directory(self):
        return self.coursedir.solution_directory

    preprocessors = List([
        IncludeHeaderFooter,
        LockCells,
        ClearOutput,
        ClearMarkScheme,
        Execute
    ])
    # NB: ClearHiddenTests must come after ComputeChecksums and SaveCells.
    # ComputerChecksums must come again after ClearHiddenTests.

    def __init__(self, coursedir: CourseDirectory = None, **kwargs: Any) -> None:
        super(GenerateSolution, self).__init__(coursedir=coursedir, **kwargs)

    def start(self) -> None:
        old_student_id = self.coursedir.student_id
        self.coursedir.student_id = '.'
        try:
            super(GenerateSolution, self).start()
        finally:
            self.coursedir.student_id = old_student_id
