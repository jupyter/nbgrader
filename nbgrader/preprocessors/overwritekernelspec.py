import json

from . import NbGraderPreprocessor
from ..api import Gradebook


class OverwriteKernelspec(NbGraderPreprocessor):
    """A preprocessor for checking the notebook kernelspec metadata."""

    def preprocess(self, nb, resources):
        # pull information from the resources
        notebook_id = resources['nbgrader']['notebook']
        assignment_id = resources['nbgrader']['assignment']
        db_url = resources['nbgrader']['db_url']

        with Gradebook(db_url) as gb:
            kernelspec = gb.find_notebook(notebook_id, assignment_id).kernelspec
            if kernelspec:
                self.log.debug(
                    "Overwriting notebook kernelspec with: {}".format(kernelspec))
                nb.metadata['kernelspec'] = json.loads(kernelspec)
        return nb, resources
