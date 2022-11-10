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

    interrupt_on_timeout = Bool(
        True,
        help=dedent(
            """
            If execution of a cell times out, interrupt the kernel and
            continue executing other cells rather than throwing an error and
            stopping.
            """
        )
    ).tag(config=True)

    allow_errors = Bool(
        True,
        help=dedent(
            """
            If ``False``, when a cell raises an error the
            execution is stopped and a ``CellExecutionError``
            is raised, except if the error name is in
            ``allow_error_names``.
            If ``True`` (default), execution errors are ignored and the execution
            is continued until the end of the notebook. Output from
            exceptions is included in the cell output in both cases.
            """
        ),
    ).tag(config=True)

    raise_on_iopub_timeout = Bool(
        True,
        help=dedent(
            """
            If ``False``, then the kernel will continue waiting for
            iopub messages until it receives a kernel idle message, or until a
            timeout occurs, at which point the currently executing cell will be
            skipped. If ``True`` (default), then an error will be raised after the first
            timeout. This option generally does not need to be used, but may be
            useful in contexts where there is the possibility of executing
            notebooks with memory-consuming infinite loops.
            """
        ),
    ).tag(config=True)

    timeout = Integer(
        30,
        allow_none=True,
        help=dedent(
            """
            The time to wait (in seconds) for output from executions.
            If a cell execution takes longer, a TimeoutError is raised.
            ``None`` or ``-1`` will disable the timeout. If ``timeout_func`` is set,
            it overrides ``timeout``.
            """
        )
    ).tag(config=True)

    error_on_timeout = {
        "ename": "CellTimeoutError",
        "evalue": "",
        "traceback": ["ERROR: No reply from kernel"]
    }

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

    def on_cell_executed(self, **kwargs):
        cell = kwargs['cell']
        reply = kwargs['execute_reply']
        if reply['content']['status'] == 'error':
            error_recorded = False
            for output in cell.outputs:
                if output.output_type == 'error':
                    error_recorded = True
            if not error_recorded:
                # Occurs when
                # IPython.core.interactiveshell.InteractiveShell.showtraceback
                # = lambda *args, **kwargs : None
                error_output = NotebookNode(output_type='error')
                error_output.ename = reply['content']['ename']
                error_output.evalue = reply['content']['evalue']
                error_output.traceback = reply['content']['traceback']
                if error_output.traceback == []:
                    error_output.traceback = ["ERROR: An error occurred while"
                                                " showtraceback was disabled"]
                cell.outputs.append(error_output)
