import nbformat
from nbformat.notebooknode import NotebookNode


class DuplicateIdError(Exception):

    def __init__(self, message):
        super(DuplicateIdError, self).__init__(message)


class CheckDuplicateFlag:

    def __init__(self, notebook_filename):
        with open(notebook_filename, encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)
        self.postprocess(nb)

    def postprocess(self, nb: NotebookNode):
        for cell in nb.cells:
            self.postprocess_cell(cell)

    @staticmethod
    def postprocess_cell(cell: NotebookNode):
        if "nbgrader" in cell.metadata and "duplicate" in cell.metadata.nbgrader:
            del cell.metadata.nbgrader["duplicate"]
            msg = "Detected cells with same ids"
            raise DuplicateIdError(msg)
