import sys
import os

from traitlets.config import LoggingConfigurable
from traitlets import List, Unicode, Integer, Bool
from nbformat import current_nbformat, read as read_nb
from textwrap import fill, dedent
from nbconvert.filters import ansi2html, strip_ansi

from .preprocessors import Execute, ClearOutput, CheckCellMetadata
from . import utils


class Validator(LoggingConfigurable):

    preprocessors = List([
        CheckCellMetadata,
        ClearOutput,
        Execute
    ])

    indent = Unicode(
        "    ",
        help="A string containing whitespace that will be used to indent code and errors"
    ).tag(config=True)

    width = Integer(
        90,
        help="Maximum line width for displaying code/errors"
    ).tag(config=True)

    invert = Bool(
        False,
        help="Complain when cells pass, rather than fail."
    ).tag(config=True)

    ignore_checksums = Bool(
        False,
        help=dedent(
            """
            Don't complain if cell checksums have changed (if they are locked
            cells) or haven't changed (if they are solution cells). Note that
            this will NOT ignore changes to cell types.
            """
        )
    ).tag(config=True)

    type_changed_warning = Unicode(
        dedent(
            """
            THE TYPES OF {num_changed} CELL(S) HAVE CHANGED!
            This might mean that even though the tests are passing
            now, they won't pass when your assignment is graded.
            """
        ).strip() + "\n",
        help="Warning to display when a cell's type has changed."
    ).tag(config=True)

    changed_warning = Unicode(
        dedent(
            """
            THE CONTENTS OF {num_changed} TEST CELL(S) HAVE CHANGED!
            This might mean that even though the tests are passing
            now, they won't pass when your assignment is graded.
            """
        ).strip() + "\n",
        help="Warning to display when a cell has changed."
    ).tag(config=True)

    failed_warning = Unicode(
        dedent(
            """
            VALIDATION FAILED ON {num_failed} CELL(S)! If you submit
            your assignment as it is, you WILL NOT receive full
            credit.
            """
        ).strip() + "\n",
        help="Warning to display when a cell fails."
    ).tag(config=True)

    passed_warning = Unicode(
        dedent(
            """
            NOTEBOOK PASSED ON {num_passed} CELL(S)!
            """
        ).strip() + "\n",
        help="Warning to display when a cell passes (when invert=True)"
    ).tag(config=True)

    validate_all = Bool(
        False,
        help="Validate all cells, not just the graded tests cells."
    ).tag(config=True)

    stream = sys.stdout

    def _indent(self, val):
        lines = val.split("\n")
        new_lines = []
        for line in lines:
            new_line = self.indent + strip_ansi(line)
            if len(new_line) > (self.width - 3):
                new_line = new_line[:(self.width - 3)] + "..."
            new_lines.append(new_line)
        return "\n".join(new_lines)

    def _extract_error(self, cell):
        errors = []

        # possibilities:
        # 1. the cell returned an error in cell.outputs
        # 2. grade cell returned score < max_points (i.e. partial credit)
        # 3. the student did not provide a response
        if cell.cell_type == "code":
            for output in cell.outputs:
                if output.output_type == "error":
                    errors.append("\n".join(output.traceback))

            if len(errors) == 0:
                if utils.is_grade(cell):
                    score, max_score = utils.determine_grade(cell, self.log)
                    if (score < max_score):
                        errors.append("Partial credit; passed some but not all of the tests")
                else:
                    errors.append("You did not provide a response.")

        else:
            errors.append("You did not provide a response.")

        return "\n".join(errors)

    def _print_type_changed(self, old_type, new_type, source):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write(
            "The following {} cell has changed to a {} cell:\n\n".format(
                old_type, new_type))
        self.stream.write(self._indent(source) + "\n\n")

    def _print_changed(self, source):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell has changed:\n\n")
        self.stream.write(self._indent(source) + "\n\n")

    def _print_error(self, source, error):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell failed:\n\n")
        self.stream.write(self._indent(source) + "\n\n")
        self.stream.write("The error was:\n\n")
        self.stream.write(self._indent(error) + "\n\n")

    def _print_pass(self, source):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell passed:\n\n")
        self.stream.write(self._indent(source) + "\n\n")

    def _print_num_type_changed(self, num_changed):
        if num_changed == 0:
            return

        else:
            self.stream.write(
                fill(
                    self.type_changed_warning.format(num_changed=num_changed),
                    width=self.width
                )
            )

    def _print_num_changed(self, num_changed):
        if num_changed == 0:
            return

        else:
            self.stream.write(
                fill(
                    self.changed_warning.format(num_changed=num_changed),
                    width=self.width
                )
            )

    def _print_num_failed(self, num_failed):
        if num_failed == 0:
            self.stream.write("Success! Your notebook passes all the tests.\n")

        else:
            self.stream.write(
                fill(
                    self.failed_warning.format(num_failed=num_failed),
                    width=self.width
                )
            )

    def _print_num_passed(self, num_passed):
        if num_passed == 0:
            self.stream.write("Success! The notebook does not pass any tests.\n")

        else:
            self.stream.write(
                fill(
                    self.passed_warning.format(num_passed=num_passed),
                    width=self.width
                )
            )

    def _get_type_changed_cells(self, nb):
        changed = []

        for cell in nb.cells:
            if not (utils.is_grade(cell) or utils.is_solution(cell) or utils.is_locked(cell)):
                continue
            if 'cell_type' not in cell.metadata.nbgrader:
                continue

            new_type = cell.metadata.nbgrader.cell_type
            old_type = cell.cell_type
            if new_type and (old_type != new_type):
                changed.append(cell)

        return changed

    def _get_changed_cells(self, nb):
        changed = []
        for cell in nb.cells:
            if not (utils.is_grade(cell) or utils.is_locked(cell)):
                continue

            # if we're ignoring checksums, then remove the checksum from the
            # cell metadata
            if self.ignore_checksums and 'checksum' in cell.metadata.nbgrader:
                del cell.metadata.nbgrader['checksum']

            # verify checksums of cells
            if utils.is_locked(cell) and 'checksum' in cell.metadata.nbgrader:
                old_checksum = cell.metadata.nbgrader['checksum']
                new_checksum = utils.compute_checksum(cell)
                if old_checksum != new_checksum:
                    changed.append(cell)

        return changed

    def _get_failed_cells(self, nb):
        failed = []
        for cell in nb.cells:
            if not (self.validate_all or utils.is_grade(cell) or utils.is_locked(cell)):
                continue

            # if it's a grade cell, the check the grade
            if utils.is_grade(cell):
                score, max_score = utils.determine_grade(cell, self.log)

                # it's a markdown cell, so we can't do anything
                if score is None:
                    pass
                elif score < max_score:
                    failed.append(cell)
            elif self.validate_all and cell.cell_type == 'code':
                for output in cell.outputs:
                    if output.output_type == 'error':
                        failed.append(cell)
                        break

        return failed

    def _get_passed_cells(self, nb):
        passed = []
        for cell in nb.cells:
            if not (utils.is_grade(cell) or utils.is_locked(cell)):
                continue

            # if it's a grade cell, the check the grade
            if utils.is_grade(cell):
                score, max_score = utils.determine_grade(cell, self.log)

                # it's a markdown cell, so we can't do anything
                if score is None:
                    pass
                elif score == max_score:
                    passed.append(cell)

        return passed

    def _preprocess(self, nb):
        resources = {}
        with utils.setenv(NBGRADER_VALIDATING='1'):
            for preprocessor in self.preprocessors:
                # https://github.com/jupyter/nbgrader/pull/1075
                # It seemes that without the self.config passed below,
                # --ExecutePreprocessor.timeout doesn't work.  Better solution
                # requested, unknown why this is needed.
                pp = preprocessor(**self.config[preprocessor.__name__])
                nb, resources = pp.preprocess(nb, resources)
        return nb

    def validate(self, filename):
        self.log.info("Validating '{}'".format(os.path.abspath(filename)))
        basename = os.path.basename(filename)
        dirname = os.path.dirname(filename)
        with utils.chdir(dirname):
            nb = read_nb(basename, as_version=current_nbformat)

        type_changed = self._get_type_changed_cells(nb)
        if len(type_changed) > 0:
            results = {}
            results['type_changed'] = [{
                "source": cell.source.strip(),
                "old_type": cell.cell_type,
                "new_type": cell.metadata.nbgrader.cell_type
            } for cell in type_changed]
            return results

        with utils.chdir(dirname):
            nb = self._preprocess(nb)
        changed = self._get_changed_cells(nb)
        passed = self._get_passed_cells(nb)
        failed = self._get_failed_cells(nb)

        results = {}

        if not self.ignore_checksums and len(changed) > 0:
            results['changed'] = [{
                "source": cell.source.strip()
            } for cell in changed]

        elif self.invert:
            if len(passed) > 0:
                results['passed'] = [{
                    "source": cell.source.strip()
                } for cell in passed]

        else:
            if len(failed) > 0:
                results['failed'] = [{
                    "source": cell.source.strip(),
                    "error": ansi2html(self._extract_error(cell)),
                    "raw_error": self._extract_error(cell)
                } for cell in failed]

        return results

    def validate_and_print(self, filename):
        results = self.validate(filename)
        type_changed = results.get('type_changed', [])
        changed = results.get('changed', [])
        passed = results.get('passed', [])
        failed = results.get('failed', [])

        if len(type_changed) > 0:
            self._print_num_type_changed(len(type_changed))
            for cell in type_changed:
                self._print_type_changed(cell['old_type'], cell['new_type'], cell['source'])

        elif not self.ignore_checksums and len(changed) > 0:
            self._print_num_changed(len(changed))
            for cell in changed:
                self._print_changed(cell['source'])

        elif self.invert:
            self._print_num_passed(len(passed))
            for cell in passed:
                self._print_pass(cell['source'])

        else:
            self._print_num_failed(len(failed))
            for cell in failed:
                self._print_error(cell['source'], cell['raw_error'])
