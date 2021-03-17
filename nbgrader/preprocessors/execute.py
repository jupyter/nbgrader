from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
from traitlets import Bool, List, Integer
from textwrap import dedent

from . import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Any, Optional, Tuple


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
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        if self.extra_arguments == [] and kernel_name == "python":
            self.extra_arguments = ["--HistoryManager.hist_file=:memory:"]

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

    def preprocess_cell(self, cell, resources, cell_index, store_history=True):
            """
            Need to override preprocess_cell to check reply for errors
            """
            # Copied from nbconvert ExecutePreprocessor
            if cell.cell_type != 'code' or not cell.source.strip():
                return cell, resources

            reply, outputs = self.run_cell(cell, cell_index, store_history)
            # Backwards compatibility for processes that wrap run_cell
            cell.outputs = outputs

            cell_allows_errors = (self.allow_errors or "raises-exception"
                                in cell.metadata.get("tags", []))

            if self.force_raise_errors or not cell_allows_errors:
                if (reply is not None) and reply['content']['status'] == 'error':
                    raise CellExecutionError.from_cell_and_msg(cell, reply['content'])

            # Ensure errors are recorded to prevent false positives when autograding
            if (reply is None) or reply['content']['status'] == 'error':
                error_recorded = False
                for output in cell.outputs:
                    if output.output_type == 'error':
                        error_recorded = True
                if not error_recorded:
                    error_output = NotebookNode(output_type='error')
                    if reply is None:
                        # Occurs when
                        # IPython.core.interactiveshell.InteractiveShell.showtraceback
                        # = None
                        error_output.ename = "CellTimeoutError"
                        error_output.evalue = ""
                        error_output.traceback = ["ERROR: No reply from kernel"]
                    else:
                        # Occurs when
                        # IPython.core.interactiveshell.InteractiveShell.showtraceback
                        # = lambda *args, **kwargs : None
                        error_output.ename = reply['content']['ename']
                        error_output.evalue = reply['content']['evalue']
                        error_output.traceback = reply['content']['traceback']
                        if error_output.traceback == []:
                            error_output.traceback = ["ERROR: An error occurred while"
                                                      " showtraceback was disabled"]
                    cell.outputs.append(error_output)

            return cell, resources
