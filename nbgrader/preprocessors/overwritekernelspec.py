import json

from . import NbGraderPreprocessor
from ..api import Gradebook
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Tuple


class OverwriteKernelspec(NbGraderPreprocessor):
    """A preprocessor for checking the notebook kernelspec metadata."""

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        notebook_id = resources['nbgrader']['notebook']
        assignment_id = resources['nbgrader']['assignment']
        db_url = resources['nbgrader']['db_url']

        with Gradebook(db_url) as gb:
            kernelspec = gb.find_notebook(notebook_id, assignment_id).kernelspec
            if kernelspec is not None:
                kernelspec = json.loads(kernelspec)

            self.log.debug("Source notebook kernelspec: {}".format(kernelspec))
            self.log.debug(
                "Submitted notebook kernelspec: {}"
                "".format(nb.metadata.get('kernelspec', None))
            )
            if kernelspec:
                self.log.debug(
                    "Overwriting submitted notebook kernelspec: {}"
                    "".format(kernelspec)
                )
                nb.metadata['kernelspec'] = kernelspec
        return nb, resources
