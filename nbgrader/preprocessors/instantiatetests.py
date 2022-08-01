import os
import yaml
import jinja2 as j2
import re
from .. import utils
from traitlets import Bool, List, Integer, Unicode, Dict, Callable
from textwrap import dedent
from . import Execute
import secrets
import asyncio
import inspect
import typing as t
from nbformat import NotebookNode
from queue import Empty
import datetime
from typing import Optional
from nbclient.exceptions import (
    CellControlSignal,
    CellExecutionComplete,
    CellExecutionError,
    CellTimeoutError,
    DeadKernelError,
)

try:
    from time import monotonic  # Py 3
except ImportError:
    from time import time as monotonic  # Py 2


#########################################################################################
class CellExecutionComplete(Exception):
    """
    Used as a control signal for cell execution across run_cell and
    process_message function calls. Raised when all execution requests
    are completed and no further messages are expected from the kernel
    over zeromq channels.
    """
    pass


#########################################################################################
class CellExecutionError(Exception):
    """
    Custom exception to propagate exceptions that are raised during
    notebook execution to the caller. This is mostly useful when
    using nbconvert as a library, since it allows dealing with
    failures gracefully.
    """

    # -------------------------------------------------------------------------------------
    def __init__(self, traceback):
        super(CellExecutionError, self).__init__(traceback)
        self.traceback = traceback

    # -------------------------------------------------------------------------------------
    def __str__(self):
        s = self.__unicode__()
        if not isinstance(s, str):
            s = s.encode('utf8', 'replace')
        return s

    # -------------------------------------------------------------------------------------
    def __unicode__(self):
        return self.traceback

    # -------------------------------------------------------------------------------------
    @classmethod
    def from_code_and_msg(cls, code, msg):
        """Instantiate from a code cell object and a message contents
        (message is either execute_reply or error)
        """
        tb = '\n'.join(msg.get('traceback', []))
        return cls(exec_err_msg.format(code=code, traceback=tb))
    # -------------------------------------------------------------------------------------


exec_err_msg = u"""\
An error occurred while executing the following code:
------------------
{code}
------------------
{traceback}
"""


#########################################################################################
class InstantiateTests(Execute):
    tests = None

    autotest_filename = Unicode(
        "tests.yml",
        help="The filename where automatic testing code is stored"
    ).tag(config=True)

    autotest_delimiter = Unicode(
        "AUTOTEST",
        help="The delimiter prior to snippets to be autotested"
    ).tag(config=True)

    hashed_delimiter = Unicode(
        "HASHED",
        help="The delimiter prior to an autotest block if snippet results should be protected by a hash function"
    ).tag(config=True)

    use_salt = Bool(
        True,
        help="Whether to add a salt to digested answers"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing autotest delimiters
            are not marked as grade cells. WARNING: disabling this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    comment_strs = Dict(
        key_trait = Unicode(),
        value_trait = Unicode(),
        default_value = {
            'ir': '#',
            'python': '#',
            'python3': '#'
        },
        help = dedent(
            """
            A dictionary mapping each Jupyter kernel's name to the comment string for that kernel.
            For an example, one of the entries in this dictionary is "python" : "#", because # is the comment
            character in python.
            """
        )
    ).tag(config=True)

    sanitizers = Dict(
        key_trait = Unicode(),
        value_trait = Callable(),
        default_value = {
            'ir': lambda s: re.sub(r'\[\d+\]\s+', '', s).strip('"').strip("'"),
            'python': lambda s: s.strip('"').strip("'"),
            'python3': lambda s: s.strip('"').strip("'")
        },
        help = dedent(
            """
            A dictionary mapping each Jupyter kernel's name to the function that is used to
            sanitize the output from the kernel within InstantiateTests.
            """
        )
    ).tag(config=True)

    sanitizer = None
    global_tests_loaded = False

    def preprocess(self, nb, resources):
        # avoid starting the kernel at all/processing the notebook if there are no autotest delimiters
        for index, cell in enumerate(nb.cells):
            # ignore non-code cells
            if cell.cell_type != 'code':
                continue
            # look for an autotest delimiter in this cell's source; if we find one, process this notebook
            if self.autotest_delimiter in cell.source:
                nb, resources = super(InstantiateTests, self).preprocess(nb, resources)
                return nb, resources
        # if not, just return
        return nb, resources

    def preprocess_cell(self, cell, resources, index):
        # new_lines will store the replacement code after autotest template instantiation
        new_lines = []

        # first, run the cell normally
        #cell, resources = super(InstantiateTests, self).preprocess_cell(cell, resources, index)

        kernel_name = self.nb.metadata.get("kernelspec", {}).get("name", "")
        if kernel_name not in self.comment_strs:
            raise ValueError(
                "kernel '{}' has not been specified in "
                "InstantiateTests.comment_strs".format(kernel_name))
        resources["kernel_name"] = kernel_name

        # if it's not a code cell, or it's empty, just return
        if cell.cell_type != 'code':
            return cell, resources

        # determine whether the cell is a grade cell
        is_grade_flag = utils.is_grade(cell)

        # get the comment string for this language
        comment_str = self.comment_strs[resources['kernel_name']]

        # split the code lines into separate strings
        lines = cell.source.split("\n")

        setup_code_inserted_into_cell = False

        non_autotest_code_lines = []

        if self.sanitizer is None:
            self.log.debug('Setting sanitizer for language ' + resources['kernel_name'])
            self.sanitizer = self.sanitizers.get(resources['kernel_name'], lambda x: x)

        for line in lines:

            # if the current line doesn't have the autotest_delimiter or is not a comment
            # then just append the line to the new cell code and go to the next line
            if self.autotest_delimiter not in line or line.strip()[:len(comment_str)] != comment_str:
                new_lines.append(line)
                non_autotest_code_lines.append(line)
                continue

            # run all code lines prior to the current line containing the autotest_delimiter
            asyncio.run(self._async_execute_code_snippet("\n".join(non_autotest_code_lines)))
            non_autotest_code_lines = []

            # there are autotests; we should check that it is a grading cell
            if not is_grade_flag:
                if not self.enforce_metadata:
                    self.log.warning(
                        "Autotest region detected in a non-grade cell; "
                        "please make sure all autotest regions are within "
                        "'Autograder tests' cells."
                    )
                else:
                    self.log.error(
                        "Autotest region detected in a non-grade cell; "
                        "please make sure all autotest regions are within "
                        "'Autograder tests' cells."
                    )
                    raise Exception

            self.log.debug('')
            self.log.debug('')
            self.log.debug('Autotest delimiter found on line. Preprocessing...')

            # the first time we run into an autotest delimiter, obtain the
            # tests object from the tests.yml template file for the assignment
            # and append any setup code to the cell block we're in
            # also figure out what language we're using

            # loading the template tests file
            if not self.global_tests_loaded:
                self.log.debug('Loading tests template file')
                self._load_test_template_file(resources)
                self.global_tests_loaded = True

            # if the setup_code is successfully obtained from the template file and
            # the current cell does not already have the setup code, add the setup_code
            if (self.setup_code is not None) and (not setup_code_inserted_into_cell):
                new_lines.append(self.setup_code)
                setup_code_inserted_into_cell = True
                asyncio.run(self._async_execute_code_snippet(self.setup_code))

            # decide whether to use hashing based on whether the self.hashed_delimiter token
            # appears in the line before the self.autotest_delimiter token
            use_hash = (self.hashed_delimiter in line[:line.find(self.autotest_delimiter)])
            if use_hash:
                self.log.debug('Hashing delimiter found, using template: ' + self.hash_template)
            else:
                self.log.debug('Hashing delimiter not found')

            # take everything after the autotest_delimiter as code snippets separated by semicolons
            snippets = [snip.strip() for snip in
                        line[line.find(self.autotest_delimiter) + len(self.autotest_delimiter):].strip(';').split(';')]

            # remove empty snippets
            if '' in snippets:
                snippets.remove('')

            # print autotest snippets to log
            self.log.debug('Found snippets to autotest: ')
            for snippet in snippets:
                self.log.debug(snippet)

            # generate the test for each snippet
            for snippet in snippets:
                self.log.debug('Running autotest generation for snippet ' + snippet)

                # create a random salt for this test
                if use_hash:
                    salt = secrets.token_hex(8)
                    self.log.debug('Using salt: ' + salt)
                else:
                    salt = None

                # get the normalized(/hashed) template tests for this code snippet
                self.log.debug(
                    'Instantiating normalized' + ('/hashed ' if use_hash else ' ') + 'test templates based on type')
                instantiated_tests, test_values, fail_messages = self._instantiate_tests(snippet, salt)

                # add all the lines to the cell
                self.log.debug('Inserting test code into cell')
                template = j2.Environment(loader=j2.BaseLoader).from_string(self.check_template)
                for i in range(len(instantiated_tests)):
                    check_code = template.render(snippet=instantiated_tests[i], value=test_values[i],
                                                 message=fail_messages[i])
                    self.log.debug('Test: ' + check_code)
                    new_lines.append(check_code)

                # add an empty line after this block of test code
                new_lines.append('')

        # run the trailing non-autotest lines, if any remain
        if len(non_autotest_code_lines) > 0:
            asyncio.run(self._async_execute_code_snippet("\n".join(non_autotest_code_lines)))

        # add the final success message
        if is_grade_flag and self.global_tests_loaded:
            if self.autotest_delimiter in cell.source:
                new_lines.append(self.success_code)

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return cell, resources

    # -------------------------------------------------------------------------------------
    def _load_test_template_file(self, resources):
        """
        attempts to load the tests.yml file within the assignment directory. In case such file is not found
        or perhaps cannot be loaded, it will attempt to load the default_tests.yaml file with the course_directory
        """
        self.log.debug('loading template tests.yml...')
        self.log.debug('kernel_name: ' + resources["kernel_name"])
        try:
            with open(os.path.join(resources['metadata']['path'], self.autotest_filename), 'r') as tests_file:
                tests = yaml.safe_load(tests_file)
            self.log.debug(tests)

        except FileNotFoundError:
            # if there is no tests file, just load a default tests dict
            self.log.warning('No tests.yml file found in the assignment directory. Loading the default tests.yml file in the course root directory')
            # tests = {}
            try:
                with open(os.path.join(self.autotest_filename), 'r') as tests_file:
                    tests = yaml.safe_load(tests_file)
            except FileNotFoundError:
                # if there is no tests file, just create a default empty tests dict
                self.log.warning(
                    'No tests.yml file found. If AUTOTESTS appears in testing cells, an error will be thrown.')
                tests = {}
            except yaml.parser.ParserError as e:
                self.log.error('tests.yml contains invalid YAML code.')
                self.log.error(e.msg)
                raise

        except yaml.parser.ParserError as e:
            self.log.error('tests.yml contains invalid YAML code.')
            self.log.error(e.msg)
            raise

        # get kernel specific data
        tests = tests[resources["kernel_name"]]

        # get the test templates
        self.test_templates_by_type = tests['templates']

        # get the test dispatch code template
        self.dispatch_template = tests['dispatch']

        # get the success message template
        self.success_code = tests['success']

        # get the hash code template
        self.hash_template = tests['hash']

        # get the hash code template
        self.check_template = tests['check']

        # get the hash code template
        self.normalize_template = tests['normalize']

        # get the setup code if it's there
        self.setup_code = tests.get('setup', None)

    # -------------------------------------------------------------------------------------
    def _instantiate_tests(self, snippet, salt=None):
        # get the type of the snippet output (used to dispatch autotest)
        template = j2.Environment(loader=j2.BaseLoader).from_string(self.dispatch_template)
        dispatch_code = template.render(snippet=snippet)
        dispatch_result = asyncio.run(self._async_execute_code_snippet(dispatch_code))
        self.log.debug('Dispatch result returned by kernel: ', dispatch_result)
        # get the test code; if the type isn't in our dict, just default to 'default'
        # if default isn't in the tests code, this will throw an error
        try:
            tests = self.test_templates_by_type.get(dispatch_result, self.test_templates_by_type['default'])
        except KeyError:
            self.log.error('tests.yml must contain a top-level "default" key with corresponding test code')
            raise
        try:
            test_templs = [t['test'] for t in tests]
            fail_msgs = [t['fail'] for t in tests]
        except KeyError:
            self.log.error('each type in tests.yml must have a list of dictionaries with a "test" and "fail" key')
            self.log.error('the "test" item should store the test template code, '
                           'and the "fail" item should store a failure message')
            raise

        #
        rendered_fail_msgs = []
        for templ in fail_msgs:
            template = j2.Environment(loader=j2.BaseLoader).from_string(templ)
            rendered_fail_msgs.append(template.render(snippet=snippet))

        # normalize the templates
        normalized_templs = []
        for templ in test_templs:
            template = j2.Environment(loader=j2.BaseLoader).from_string(self.normalize_template)
            normalized_templs.append(template.render(snippet=templ))

        # hashify the templates
        processed_templs = []
        if salt is not None:
            for templ in normalized_templs:
                template = j2.Environment(loader=j2.BaseLoader).from_string(self.hash_template)
                processed_templs.append(template.render(snippet=templ, salt=salt))
        else:
            processed_templs = normalized_templs

        # instantiate and evaluate the tests
        instantiated_tests = []
        test_values = []
        for templ in processed_templs:
            # instantiate the template snippet
            template = j2.Environment(loader=j2.BaseLoader).from_string(templ)
            instantiated_test = template.render(snippet=snippet)
            # run the instantiated template code
            test_value = asyncio.run(self._async_execute_code_snippet(instantiated_test))
            instantiated_tests.append(instantiated_test)
            test_values.append(test_value)

        return instantiated_tests, test_values, rendered_fail_msgs

    # -------------------------------------------------------------------------------------

    #########################
    # async version of nbgrader interaction with kernel
    # the below functions were adapted from the jupyter/nbclient GitHub repo, commit:
    # https://github.com/jupyter/nbclient/commit/0c08e27c1ec655cffe9b35cf637da742cdab36e8
    #########################

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.util.ensure_async
    async def _ensure_async(self, obj):
        """Convert a non-awaitable object to a coroutine if needed,
        and await it if it was not already awaited.
        adapted from nbclient.util._ensure_async
        """
        if inspect.isawaitable(obj):
            try:
                result = await obj
            except RuntimeError as e:
                if str(e) == 'cannot reuse already awaited coroutine':
                    return obj
                raise
            return result
        return obj

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client._async_handle_timeout
    async def _async_handle_timeout(self, timeout: int) -> None:

        self.log.error("Timeout waiting for execute reply (%is)." % timeout)
        if self.interrupt_on_timeout:
            self.log.error("Interrupting kernel")
            assert self.km is not None
            await _ensure_async(self.km.interrupt_kernel())
        else:
            raise CellTimeoutError.error_from_timeout_and_cell(
                "Cell execution timed out", timeout
            )

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client._async_check_alive
    async def _async_check_alive(self) -> None:
        assert self.kc is not None
        if not await self._ensure_async(self.kc.is_alive()):
            self.log.error("Kernel died while waiting for execute reply.")
            raise DeadKernelError("Kernel died")

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client._async_poll_output_msg
    async def _async_poll_output_msg_code(
            self, parent_msg_id: str, code
    ) -> None:

        assert self.kc is not None
        while True:
            msg = await self._ensure_async(self.kc.iopub_channel.get_msg(timeout=None))
            if msg['parent_header'].get('msg_id') == parent_msg_id:
                try:
                    msg_type = msg['msg_type']
                    self.log.debug("msg_type: %s", msg_type)
                    content = msg['content']
                    self.log.debug("content: %s", content)

                    if msg_type in {'execute_result', 'display_data', 'update_display_data'}:
                        return self.sanitizer(content['data']['text/plain'])

                    if msg_type == 'error':
                        self.log.error("Failed to run code: \n%s", code)
                        self.log.error("Runtime error from the kernel: \n%s", content['evalue'])
                        break

                    if msg_type == 'status':
                        if content['execution_state'] == 'idle':
                            raise CellExecutionComplete()

                except CellExecutionComplete:
                    return

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client.async_wait_for_reply
    async def _async_wait_for_reply(
            self, msg_id: str, cell: t.Optional[NotebookNode] = None
    ) -> t.Optional[t.Dict]:

        assert self.kc is not None
        # wait for finish, with timeout
        timeout = self._get_timeout(cell)
        cummulative_time = 0
        while True:
            try:
                msg = await _ensure_async(
                    self.kc.shell_channel.get_msg(timeout=self.shell_timeout_interval)
                )
            except Empty:
                await self._async_check_alive()
                cummulative_time += self.shell_timeout_interval
                if timeout and cummulative_time > timeout:
                    await self._async_async_handle_timeout(timeout, cell)
                    break
            else:
                if msg['parent_header'].get('msg_id') == msg_id:
                    return msg
        return None

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client._async_poll_for_reply
    async def _async_poll_for_reply_code(
            self,
            msg_id: str,
            timeout: t.Optional[int],
            task_poll_output_msg: asyncio.Future,
            task_poll_kernel_alive: asyncio.Future,
    ) -> t.Dict:

        assert self.kc is not None

        self.log.debug("Executing _async_poll_for_reply:\n%s", msg_id)

        if timeout is not None:
            deadline = monotonic() + timeout
            new_timeout = float(timeout)

        while True:
            try:
                shell_msg = await self._ensure_async(self.kc.shell_channel.get_msg(timeout=new_timeout))
                if shell_msg['parent_header'].get('msg_id') == msg_id:
                    try:
                        msg = await asyncio.wait_for(task_poll_output_msg, new_timeout)
                    except (asyncio.TimeoutError, Empty):
                        task_poll_kernel_alive.cancel()
                        raise CellExecutionError("Timeout waiting for IOPub output")
                    self.log.debug("Get _async_poll_for_reply:\n%s", msg)

                    return msg if msg != None else ""
                else:
                    if new_timeout is not None:
                        new_timeout = max(0, deadline - monotonic())
            except Empty:
                self.log.debug("Empty _async_poll_for_reply:\n%s", msg_id)
                task_poll_kernel_alive.cancel()
                await self._async_check_alive()
                await self._async_handle_timeout()

    # -------------------------------------------------------------------------------------
    # adapted from nbclient.client.async_execute_cell
    async def _async_execute_code_snippet(self, code):
        assert self.kc is not None

        self.log.debug("Executing cell:\n%s", code)

        parent_msg_id = await self._ensure_async(self.kc.execute(code, stop_on_error=not self.allow_errors))

        task_poll_kernel_alive = asyncio.ensure_future(self._async_check_alive())

        task_poll_output_msg = asyncio.ensure_future(self._async_poll_output_msg_code(parent_msg_id, code))

        task_poll_for_reply = asyncio.ensure_future(
            self._async_poll_for_reply_code(parent_msg_id, self.timeout, task_poll_output_msg, task_poll_kernel_alive))

        try:
            msg = await task_poll_for_reply
        except asyncio.CancelledError:
            # can only be cancelled by task_poll_kernel_alive when the kernel is dead
            task_poll_output_msg.cancel()
            raise DeadKernelError("Kernel died")
        except Exception as e:
            # Best effort to cancel request if it hasn't been resolved
            try:
                # Check if the task_poll_output is doing the raising for us
                if not isinstance(e, CellControlSignal):
                    task_poll_output_msg.cancel()
            finally:
                raise

        return msg

    # -------------------------------------------------------------------------------------
    async def async_execute_cell(
            self,
            cell: NotebookNode,
            cell_index: int,
            execution_count: t.Optional[int] = None,
            store_history: bool = True,
    ) -> NotebookNode:
        """
        Executes a single code cell.

        To execute all cells see :meth:`execute`.

        Parameters
        ----------
        cell : nbformat.NotebookNode
            The cell which is currently being processed.
        cell_index : int
            The position of the cell within the notebook object.
        execution_count : int
            The execution count to be assigned to the cell (default: Use kernel response)
        store_history : bool
            Determines if history should be stored in the kernel (default: False).
            Specific to ipython kernels, which can store command histories.

        Returns
        -------
        output : dict
            The execution output payload (or None for no output).

        Raises
        ------
        CellExecutionError
            If execution failed and should raise an exception, this will be raised
            with defaults about the failure.

        Returns
        -------
        cell : NotebookNode
            The cell which was just processed.
        """
        assert self.kc is not None

        await run_hook(self.on_cell_start, cell=cell, cell_index=cell_index)

        if cell.cell_type != 'code' or not cell.source.strip():
            self.log.debug("Skipping non-executing cell %s", cell_index)
            return cell

        if self.skip_cells_with_tag in cell.metadata.get("tags", []):
            self.log.debug("Skipping tagged cell %s", cell_index)
            return cell

        if self.record_timing:  # clear execution metadata prior to execution
            cell['metadata']['execution'] = {}

        self.log.debug("Executing cell:\n%s", cell.source)

        cell_allows_errors = (not self.force_raise_errors) and (
                self.allow_errors or "raises-exception" in cell.metadata.get("tags", [])
        )

        await run_hook(self.on_cell_execute, cell=cell, cell_index=cell_index)
        parent_msg_id = await _ensure_async(
            self.kc.execute(
                cell.source, store_history=store_history, stop_on_error=not cell_allows_errors
            )
        )
        await run_hook(self.on_cell_complete, cell=cell, cell_index=cell_index)
        # We launched a code cell to execute
        self.code_cells_executed += 1
        exec_timeout = self._get_timeout(cell)

        cell.outputs = []
        self.clear_before_next_output = False

        task_poll_kernel_alive = asyncio.ensure_future(self._async_poll_kernel_alive())
        task_poll_output_msg = asyncio.ensure_future(
            self._async_poll_output_msg_code(parent_msg_id, code)
        )
        self.task_poll_for_reply = asyncio.ensure_future(
            self._async_poll_for_reply_code(
                parent_msg_id, exec_timeout, task_poll_output_msg, task_poll_kernel_alive
            )
        )
        try:
            exec_reply = await self.task_poll_for_reply
        except asyncio.CancelledError:
            # can only be cancelled by task_poll_kernel_alive when the kernel is dead
            task_poll_output_msg.cancel()
            raise DeadKernelError("Kernel died")
        except Exception as e:
            # Best effort to cancel request if it hasn't been resolved
            try:
                # Check if the task_poll_output is doing the raising for us
                if not isinstance(e, CellControlSignal):
                    task_poll_output_msg.cancel()
            finally:
                raise

        if execution_count:
            cell['execution_count'] = execution_count
        await self._check_raise_for_error(cell, cell_index, exec_reply)
        self.nb['cells'][cell_index] = cell
        return cell
    # -------------------------------------------------------------------------------------


def timestamp(msg: Optional[Dict] = None) -> str:
    if msg and 'header' in msg:  # The test mocks don't provide a header, so tolerate that
        msg_header = msg['header']
        if 'date' in msg_header and isinstance(msg_header['date'], datetime.datetime):
            try:
                # reformat datetime into expected format
                formatted_time = datetime.datetime.strftime(
                    msg_header['date'], '%Y-%m-%dT%H:%M:%S.%fZ'
                )
                if (
                        formatted_time
                ):  # docs indicate strftime may return empty string, so let's catch that too
                    return formatted_time
            except Exception:
                pass  # fallback to a local time

    return datetime.datetime.utcnow().isoformat() + 'Z'
