from IPython.nbconvert.preprocessors import ExecutePreprocessor
from IPython.utils.traitlets import Bool, List

from nbgrader.preprocessors import NbGraderPreprocessor

class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    interrupt_on_timeout = Bool(True)
    extra_arguments = List(["--HistoryManager.hist_file=:memory:"])
