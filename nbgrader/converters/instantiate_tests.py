import os
import re
from textwrap import dedent

from traitlets import List, Bool, default

from ..api import Gradebook, MissingEntry
from .base import BaseConverter, NbGraderException
from ..preprocessors import (
    InstantiateTests,
    ClearOutput,
    CheckCellMetadata
)
from traitlets.config.loader import Config
from typing import Any
from ..coursedir import CourseDirectory


class InstantiateTests(BaseConverter):

    @default("permissions")
    def _permissions_default(self) -> int:
        return 664 if self.coursedir.groupshared else 644

    @property
    def _input_directory(self) -> str:
        return self.coursedir.source_directory

    @property
    def _output_directory(self) -> str:
        return self.coursedir.instantiated_directory

    preprocessors = List([
        InstantiateTests,
        ClearOutput,
        CheckCellMetadata,
    ]).tag(config=True)

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super(InstantiateTests, self)._load_config(cfg, **kwargs)

    def __init__(self, coursedir: CourseDirectory = None, **kwargs: Any) -> None:
        super(InstantiateTests, self).__init__(coursedir=coursedir, **kwargs)

    def start(self) -> None:
        old_student_id = self.coursedir.student_id
        self.coursedir.student_id = '.'
        try:
            super(InstantiateTests, self).start()
        finally:
            self.coursedir.student_id = old_student_id
