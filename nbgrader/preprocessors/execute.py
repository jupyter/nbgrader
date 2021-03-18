from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
from traitlets import Bool, List, Integer
from textwrap import dedent

from . import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Any, Optional, Tuple, Dict


class UnresponsiveKernelError(Exception):
    pass


class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    interrupt_on_timeout = Bool(True)
    allow_errors = Bool(True)
    raise_on_iopub_timeout = Bool(True)
    extra_arguments = List([], help=dedent(
        """
        A list of extra arguments to pass to the kernel. For python kernels,
        this defaults to ``--HistoryManager.hist_file=:memory:``. For other
        kernels this is just an empty list.
        """)
    ).tag(config=True)

    execute_retries = Integer(0, help=dedent(
        """
        The number of times to try re-executing the notebook before throwing
        an error. Generally, this shouldn't need to be set, but might be useful
        for CI environments when tests are flaky.
        """)
    ).tag(config=True)

    def preprocess(self,
                   nb: NotebookNode,
                   resources: ResourcesDict,
                   retries: Optional[Any] = None
                   ) -> Tuple[NotebookNode, ResourcesDict]:
        # This gets added in by the parent execute preprocessor, so if it's already in our
        # extra arguments we need to delete it or traitlets will be unhappy.
        if '--HistoryManager.hist_file=:memory:' in self.extra_arguments:
            self.extra_arguments.remove('--HistoryManager.hist_file=:memory:')

        if retries is None:
            retries = self.execute_retries

        try:
            output = super(Execute, self).preprocess(nb, resources)
        except RuntimeError:
            if retries == 0:
                raise UnresponsiveKernelError()
            else:
                self.log.warning("Failed to execute notebook, trying again...")
                return self.preprocess(nb, resources, retries=retries - 1)

        return output

    def _check_raise_for_error(
            self,
            cell: NotebookNode,
            exec_reply: Optional[Dict]) -> None:

        exec_reply_content = None
        if exec_reply is not None:
            exec_reply_content = exec_reply['content']
            if exec_reply_content['status'] != 'error':
                return None

            cell_allows_errors = (not self.force_raise_errors) and (
                self.allow_errors
                or exec_reply_content.get('ename') in self.allow_error_names
                or "raises-exception" in cell.metadata.get("tags", []))

            if not cell_allows_errors:
                raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)

        # Ensure errors are recorded to prevent false positives when autograding
        if exec_reply is None or exec_reply_content['status'] == 'error':
            error_recorded = False
            for output in cell.outputs:
                if output.output_type == 'error':
                    error_recorded = True
                    break

            if not error_recorded:
                error_output = NotebookNode(output_type='error')
                if exec_reply is None:
                    # Occurs when
                    # IPython.core.interactiveshell.InteractiveShell.showtraceback = None
                    error_output.ename = "CellTimeoutError"
                    error_output.evalue = ""
                    error_output.traceback = ["ERROR: No reply from kernel"]
                else:
                    # Occurs when
                    # IPython.core.interactiveshell.InteractiveShell.showtraceback = lambda *args, **kwargs: None
                    error_output.ename = exec_reply_content['ename']
                    error_output.evalue = exec_reply_content['evalue']
                    error_output.traceback = exec_reply_content['traceback']
                    if error_output.traceback == []:
                        error_output.traceback = ["ERROR: An error occurred while"
                                                  " showtraceback was disabled"]
                cell.outputs.append(error_output)
