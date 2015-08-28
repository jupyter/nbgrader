import sys
import json

from traitlets import Unicode, Integer, Bool
from nbconvert.filters import ansi2html, strip_ansi

from .. import utils
from . import NbGraderPreprocessor

from textwrap import fill, dedent


class DisplayAutoGrades(NbGraderPreprocessor):
    """Preprocessor for displaying the autograder grades"""

    indent = Unicode(
        "    ",
        config=True,
        help="A string containing whitespace that will be used to indent code and errors")

    width = Integer(
        90,
        config=True,
        help="Maximum line width for displaying code/errors")

    invert = Bool(
        False,
        config=True,
        help="Complain when cells pass, rather than fail.")

    ignore_checksums = Bool(
        False, config=True,
        help=dedent(
            """
            Don't complain if cell checksums have changed (if they are locked
            cells) or haven't changed (if they are solution cells)
            """
        )
    )

    changed_warning = Unicode(
        dedent(
            """
            THE CONTENTS OF {num_changed} TEST CELL(S) HAVE CHANGED!
            This might mean that even though the tests are passing
            now, they won't pass when your assignment is graded.
            """
        ).strip() + "\n",
        config=True,
        help="Warning to display when a cell has changed.")

    failed_warning = Unicode(
        dedent(
            """
            VALIDATION FAILED ON {num_failed} CELL(S)! If you submit
            your assignment as it is, you WILL NOT receive full
            credit.
            """
        ).strip() + "\n",
        config=True,
        help="Warning to display when a cell fails.")

    passed_warning = Unicode(
        dedent(
            """
            NOTEBOOK PASSED ON {num_passed} CELL(S)!
            """
        ).strip() + "\n",
        config=True,
        help="Warning to display when a cell passes (when invert=True)")

    as_json = Bool(False, config=True, help="Print out validation results as json")

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
        if cell.cell_type == "code":
            for output in cell.outputs:
                if output.output_type == "error":
                    errors.append("\n".join(output.traceback))

            if len(errors) == 0:
                errors.append("You did not provide a response.")

        else:
            errors.append("You did not provide a response.")

        return "\n".join(errors)

    def _print_changed(self, cell):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell has changed:\n\n")
        self.stream.write(self._indent(cell.source.strip()) + "\n\n")

    def _print_error(self, cell):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell failed:\n\n")
        self.stream.write(self._indent(cell.source.strip()) + "\n\n")
        self.stream.write("The error was:\n\n")
        self.stream.write(self._indent(self._extract_error(cell)) + "\n\n")

    def _print_pass(self, cell):
        self.stream.write("\n" + "=" * self.width + "\n")
        self.stream.write("The following cell passed:\n\n")
        self.stream.write(self._indent(cell.source.strip()) + "\n\n")

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

    def preprocess(self, nb, resources):
        if 'nbgrader' not in resources:
            resources['nbgrader'] = {}

        resources['nbgrader']['failed_cells'] = []
        resources['nbgrader']['passed_cells'] = []
        resources['nbgrader']['checksum_mismatch'] = []

        nb, resources = super(DisplayAutoGrades, self).preprocess(nb, resources)

        changed = resources['nbgrader']['checksum_mismatch']
        failed = resources['nbgrader']['failed_cells']
        passed = resources['nbgrader']['passed_cells']

        json_dict = {}

        if not self.ignore_checksums and len(changed) > 0:
            if self.as_json:
                json_dict['changed'] = [{
                    "source": cell.source.strip()
                } for cell in changed]
            else:
                self._print_num_changed(len(changed))
                for cell in changed:
                    self._print_changed(cell)

        elif self.invert:
            if self.as_json:
                if len(passed) > 0:
                    json_dict['passed'] = [{
                        "source": cell.source.strip()
                    } for cell in passed]
            else:
                self._print_num_passed(len(passed))
                for cell in passed:
                    self._print_pass(cell)

        else:
            if self.as_json:
                if len(failed) > 0:
                    json_dict['failed'] = [{
                        "source": cell.source.strip(),
                        "error": ansi2html(self._extract_error(cell))
                    } for cell in failed]
            else:
                self._print_num_failed(len(failed))
                for cell in failed:
                    self._print_error(cell)

        if self.as_json:
            self.stream.write(json.dumps(json_dict))

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if not (utils.is_grade(cell) or utils.is_locked(cell)):
            return cell, resources

        # if we're ignoring checksums, then remove the checksum from the
        # cell metadata
        if self.ignore_checksums and 'checksum' in cell.metadata.nbgrader:
            del cell.metadata.nbgrader['checksum']

        # verify checksums of cells
        if utils.is_locked(cell) and 'checksum' in cell.metadata.nbgrader:
            old_checksum = cell.metadata.nbgrader['checksum']
            new_checksum = utils.compute_checksum(cell)
            if old_checksum != new_checksum:
                resources['nbgrader']['checksum_mismatch'].append(cell)

        # if it's a grade cell, the check the grade
        if utils.is_grade(cell):
            score, max_score = utils.determine_grade(cell)

            # it's a markdown cell, so we can't do anything
            if score is None:
                pass
            elif score < max_score:
                resources['nbgrader']['failed_cells'].append(cell)
            else:
                resources['nbgrader']['passed_cells'].append(cell)

        return cell, resources
