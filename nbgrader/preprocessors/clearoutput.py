from nbconvert.preprocessors import ClearOutputPreprocessor
from nbgrader.preprocessors import NbGraderPreprocessor

class ClearOutput(NbGraderPreprocessor, ClearOutputPreprocessor):
    pass