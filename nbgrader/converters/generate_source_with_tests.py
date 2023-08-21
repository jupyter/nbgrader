import os
import re

from traitlets import List, default

from .base import BaseConverter
from ..preprocessors import (
    InstantiateTests,
    ClearOutput,
    CheckCellMetadata
)
from traitlets.config.loader import Config
from typing import Any
from ..coursedir import CourseDirectory


class GenerateSourceWithTests(BaseConverter):

    @default("permissions")
    def _permissions_default(self) -> int:
        return 664 if self.coursedir.groupshared else 644

    @property
    def _input_directory(self) -> str:
        return self.coursedir.source_directory

    @property
    def _output_directory(self) -> str:
        return self.coursedir.release_directory

    preprocessors = List([
        InstantiateTests,
        ClearOutput,
        CheckCellMetadata
    ]).tag(config=True)

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        super(GenerateSourceWithTests, self)._load_config(cfg, **kwargs)

    def __init__(self, coursedir: CourseDirectory = None, **kwargs: Any) -> None:
        super(GenerateSourceWithTests, self).__init__(coursedir=coursedir, **kwargs)

    def start(self) -> None:
        old_student_id = self.coursedir.student_id
        self.coursedir.student_id = '.'
        try:
            super(GenerateSourceWithTests, self).start()
        finally:
            self.coursedir.student_id = old_student_id
