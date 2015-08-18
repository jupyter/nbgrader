from nbconvert.preprocessors import ExecutePreprocessor
from traitlets import Bool, List

from nbgrader.preprocessors import NbGraderPreprocessor

class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    interrupt_on_timeout = Bool(True)
    allow_errors = Bool(True)
    extra_arguments = List(["--HistoryManager.hist_file=:memory:"])
