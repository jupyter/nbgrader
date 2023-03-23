from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
from traitlets import Bool, List, Integer, validate, TraitError
from textwrap import dedent

from . import NbGraderPreprocessor
from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from typing import Any, Optional, Tuple


class UnresponsiveKernelError(Exception):
    pass


class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    timeout = Integer(
        30,
        help=ExecutePreprocessor.timeout.help,
        allow_none=True,
    ).tag(config=True)

    interrupt_on_timeout = Bool(
        True,
        help=ExecutePreprocessor.interrupt_on_timeout.help
    ).tag(config=True)

    allow_errors = Bool(
        True,
        help=dedent(
            """
            When a cell execution results in an error, continue executing the rest of
            the notebook. If False, the thrown nbclient exception would break aspects of
            output rendering.
            """
        ),
    )

    raise_on_iopub_timeout = Bool(
        True,
        help=ExecutePreprocessor.raise_on_iopub_timeout.help
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
