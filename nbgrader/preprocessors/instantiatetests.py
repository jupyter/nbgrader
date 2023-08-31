import os
import yaml
import jinja2 as j2
import re
from .. import utils
from traitlets import Bool, List, Integer, Unicode, Dict, Callable
from textwrap import dedent
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
from . import NbGraderPreprocessor
from jupyter_client.manager import start_new_kernel

try:
    from time import monotonic  # Py 3
except ImportError:
    from time import time as monotonic  # Py 2

#########################################################################################
class InstantiateTests(NbGraderPreprocessor):
    tests = None

    autotest_filename = Unicode(
        "autotests.yml",
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
        key_trait=Unicode(),
        value_trait=Unicode(),
        default_value={
            'ir': '#',
            'python': '#',
            'python3': '#'
        },
        help=dedent(
            """
            A dictionary mapping each Jupyter kernel's name to the comment string for that kernel.
            For an example, one of the entries in this dictionary is "python" : "#", because # is the comment
            character in python.
            """
        )
    ).tag(config=True)

    sanitizers = Dict(
        key_trait=Unicode(),
        value_trait=Callable(),
        default_value={
            'ir': lambda s: re.sub(r'\[\d+\]\s+', '', s).strip('"').strip("'"),
            'python': lambda s: s.strip('"').strip("'"),
            'python3': lambda s: s.strip('"').strip("'")
        },
        help=dedent(
            """
            A dictionary mapping each Jupyter kernel's name to the function that is used to
            sanitize the output from the kernel within InstantiateTests.
            """
        )
    ).tag(config=True)

    sanitizer = None
    kernel_name = None
    kc = None
    execute_result = None

    def preprocess(self, nb, resources):
        # avoid starting the kernel at all/processing the notebook if there are no autotest delimiters
        for index, cell in enumerate(nb.cells):
            # look for an autotest delimiter in this cell's source; if we find one, process this notebook
            # short-circuit ignore non-code cells
            if (cell.cell_type == 'code') and (self.autotest_delimiter in cell.source):
                # get the kernel name from the notebook
                kernel_name = nb.metadata.get("kernelspec", {}).get("name", "")
                if kernel_name not in self.comment_strs:
                    raise ValueError(f"Kernel {kernel_name} has not been specified in InstantiateTests.comment_strs")
                if kernel_name not in self.sanitizers:
                    raise ValueError(f"Kernel {kernel_name} has not been specified in InstantiateTests.sanitizers")
                self.log.debug("Found kernel %s", kernel_name)
                resources["kernel_name"] = kernel_name

                # get the resources path from the notebook
                resources_path = resources.get('metadata', {}).get('path', None)

                # load the template tests file
                self.log.debug('Loading template tests file')
                self._load_test_template_file(resources)
                self.global_tests_loaded = True

                # set up the sanitizer
                self.log.debug('Setting sanitizer for kernel %s', kernel_name)
                self.sanitizer = self.sanitizers[kernel_name]
                #start the kernel with the specified kernel and in the local path of the notebook
                self.log.debug('Starting client for kernel %s at path %s', kernel_name, resources_path if resources_path is not None else '')
                km, self.kc = start_new_kernel(kernel_name=kernel_name, cwd=resources_path)

                # run the preprocessor
                self.log.debug('Running InstantiateTests preprocessor')
                nb, resources = super(InstantiateTests, self).preprocess(nb, resources)

                # shut down and cleanup the kernel
                self.log.debug('Shutting down / cleaning up kernel')
                km.shutdown_kernel()
                self.kc = None
                self.sanitizer = None
                self.execute_result = None

                # return the modified notebook
                return nb, resources

        # if not, just return
        return nb, resources

    def preprocess_cell(self, cell, resources, index):
        # if it's not a code cell, or if the cell's source is empty, just return
        if (cell.cell_type != 'code') or (len(cell.source) == 0):
            return cell, resources

        # determine whether the cell is a grade cell
        is_grade_flag = utils.is_grade(cell)

        # get the comment string for this language
        comment_str = self.comment_strs[resources["kernel_name"]]

        # split the code lines into separate strings
        lines = cell.source.split("\n")

        setup_code_inserted_into_cell = False

        non_autotest_code_lines = []

        # new_lines will store the replacement code after autotest template instantiation
        new_lines = []

        for line in lines:
            # if the current line doesn't have the autotest_delimiter or is not a comment
            # then just append the line to the new cell code and go to the next line
            if self.autotest_delimiter not in line or line.strip()[:len(comment_str)] != comment_str:
                new_lines.append(line)
                non_autotest_code_lines.append(line)
                continue

            # run all code lines prior to the current line containing the autotest_delimiter
            self._execute_code_snippet("\n".join(non_autotest_code_lines))
            non_autotest_code_lines = []

            # there are autotests; we should check that it is a grading cell
            if not is_grade_flag:
                if not self.enforce_metadata:
                    self.log.warning(
                        "AutoTest region detected in a non-grade cell; "
                        "please make sure all autotest regions are within "
                        "'Autograder tests' cells."
                    )
                else:
                    self.log.error(
                        "AutoTest region detected in a non-grade cell; "
                        "please make sure all autotest regions are within "
                        "'Autograder tests' cells."
                    )
                    raise Exception

            self.log.debug('')
            self.log.debug('')
            self.log.debug('AutoTest delimiter found on line. Preprocessing...')

            # the first time we run into an autotest delimiter,
            # append any setup code to the cell block we're in

            # if the setup_code is successfully obtained from the template file and
            # the current cell does not already have the setup code, add the setup_code
            if (self.setup_code is not None) and (not setup_code_inserted_into_cell):
                new_lines.append(self.setup_code)
                setup_code_inserted_into_cell = True
                self._execute_code_snippet(self.setup_code)

            # decide whether to use hashing based on whether the self.hashed_delimiter token
            # appears in the line before the self.autotest_delimiter token
            use_hash = (self.hashed_delimiter in line[:line.find(self.autotest_delimiter)])
            if use_hash:
                if self.hash_template is None:
                    raise ValueError('Found a hashing delimiter, but the hash property has not been set in autotests.yml')
                self.log.debug('Hashing delimiter found, using template: %s', self.hash_template)
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
                self.log.debug('Running autotest generation for snippet %s', snippet)

                # create a random salt for this test
                if use_hash:
                    salt = secrets.token_hex(8)
                    self.log.debug('Using salt: %s', salt)
                else:
                    salt = None

                # get the normalized(/hashed) template tests for this code snippet
                self.log.debug(
                    'Instantiating normalized%s test templates based on type', ' & hashed' if use_hash else '')
                instantiated_tests, test_values, fail_messages = self._instantiate_tests(snippet, salt)

                # add all the lines to the cell
                self.log.debug('Inserting test code into cell')
                template = j2.Environment(loader=j2.BaseLoader).from_string(self.check_template)
                for i in range(len(instantiated_tests)):
                    check_code = template.render(snippet=instantiated_tests[i], value=test_values[i],
                                                 message=fail_messages[i])
                    self.log.debug('Test: %s', check_code)
                    new_lines.append(check_code)

                # add an empty line after this block of test code
                new_lines.append('')

        # add the final success code and execute it
        if (
            is_grade_flag
            and self.global_tests_loaded
            and (self.autotest_delimiter in cell.source)
            and (self.success_code is not None)
        ):
            new_lines.append(self.success_code)
            non_autotest_code_lines.append(self.success_code)

        # run the trailing non-autotest lines, if any remain
        if len(non_autotest_code_lines) > 0:
            self._execute_code_snippet("\n".join(non_autotest_code_lines))

        # replace the cell source
        cell.source = "\n".join(new_lines)

        # remove the execution metainfo
        cell.pop('execution', None)

        return cell, resources

    # -------------------------------------------------------------------------------------
    def _load_test_template_file(self, resources):
        """
        attempts to load the autotests.yml file within the assignment directory. In case such file is not found
        or perhaps cannot be loaded, it will attempt to load the default_tests.yaml file with the course_directory
        """
        self.log.debug('loading template autotests.yml...')
        self.log.debug('kernel_name: %s', resources["kernel_name"])
        try:
            with open(os.path.join(resources['metadata']['path'], self.autotest_filename), 'r') as tests_file:
                tests = yaml.safe_load(tests_file)
            self.log.debug(tests)

        except FileNotFoundError:
            # if there is no tests file, try to load default tests dict
            self.log.warning(
                'No autotests.yml file found in the assignment directory. Loading the default autotests.yml file in the course root directory')
            try:
                with open(os.path.join(self.autotest_filename), 'r') as tests_file:
                    tests = yaml.safe_load(tests_file)
            except FileNotFoundError:
                # if there is not even a default tests file, re-raise the FileNotFound error
                self.log.error('No autotests.yml file found, but there were autotest directives found in the notebook. ')
                raise
            except yaml.parser.ParserError as e:
                self.log.error('autotests.yml contains invalid YAML code.')
                self.log.error(e.msg)
                raise

        except yaml.parser.ParserError as e:
            self.log.error('autotests.yml contains invalid YAML code.')
            self.log.error(e.msg)
            raise

        # get kernel specific data
        tests = tests[resources["kernel_name"]]

        # get the test templates
        self.test_templates_by_type = tests['templates']

        # get the test dispatch code template
        self.dispatch_template = tests['dispatch']

        # get the success message template
        self.success_code = tests.get('success', None)

        # get the hash code template
        self.hash_template = tests.get('hash', None)

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
        dispatch_result = self._execute_code_snippet(dispatch_code)
        self.log.debug('Dispatch result returned by kernel: %s', dispatch_result)
        # get the test code; if the type isn't in our dict, just default to 'default'
        # if default isn't in the tests code, this will throw an error
        try:
            tests = self.test_templates_by_type.get(dispatch_result, self.test_templates_by_type['default'])
        except KeyError:
            self.log.error('autotests.yml must contain a top-level "default" key with corresponding test code')
            raise
        try:
            test_templs = [t['test'] for t in tests]
            fail_msgs = [t['fail'] for t in tests]
        except KeyError:
            self.log.error('each type in autotests.yml must have a list of dictionaries with a "test" and "fail" key')
            self.log.error('the "test" item should store the test template code, '
                           'and the "fail" item should store a failure message')
            raise

        #
        rendered_fail_msgs = []
        for templ in fail_msgs:
            template = j2.Environment(loader=j2.BaseLoader).from_string(templ)
            fmsg = template.render(snippet=snippet)
            # escape double quotes
            fmsg = fmsg.replace("\"", "\\\"")
            rendered_fail_msgs.append(fmsg)

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
            test_value = self._execute_code_snippet(instantiated_test)
            instantiated_tests.append(instantiated_test)
            test_values.append(test_value)

        return instantiated_tests, test_values, rendered_fail_msgs

    def _execute_code_snippet(self, code):
        self.log.debug("Executing code:\n%s", code)
        self.kc.execute_interactive(code, output_hook = self._execute_code_snippet_output_hook)
        res = self.execute_result
        self.execute_result = None
        self.log.debug("Result:\n%s", res)
        return res

    def _execute_code_snippet_output_hook(self, msg: t.Dict[str, t.Any]) -> None:
        msg_type = msg["header"]["msg_type"]
        content = msg["content"]
        if msg_type == "stream":
            pass
            #stream = getattr(sys, content["name"])
            #stream.write(content["text"])
        elif msg_type in ("display_data", "update_display_data", "execute_result"):
            self.execute_result = self.sanitizer(content["data"]["text/plain"])
        elif msg_type == "error":
            self.log.error("Runtime error from the kernel: \n%s\n%s\n%s", content['ename'], content['evalue'], content['traceback'])
            raise CellExecutionError(content['traceback'], content['ename'], content['evalue'])
        return
