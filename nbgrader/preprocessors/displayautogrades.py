import re

from IPython.utils.traitlets import Unicode, Integer, Bool

from nbgrader import utils
from nbgrader.preprocessors import NbGraderPreprocessor

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
        ).strip(),
        config=True,
        help="Warning to display when a cell has changed.")

    failed_warning = Unicode(
        dedent(
            """
            VALIDATION FAILED ON {num_failed} CELL(S)! If you submit
            your assignment as it is, you WILL NOT receive full
            credit.
            """
        ).strip(),
        config=True,
        help="Warning to display when a cell fails.")

    passed_warning = Unicode(
        dedent(
            """
            NOTEBOOK PASSED ON {num_passed} CELL(S)!
            """
        ).strip(),
        config=True,
        help="Warning to display when a cell passes (when invert=True)")

    ansi_escape = re.compile(r'\x1b[^m]*m')

    def _indent(self, val):
        lines = val.split("\n")
        new_lines = []
        for line in lines:
            new_line = self.ansi_escape.sub('', self.indent + line)
            if len(new_line) > (self.width - 3):
                new_line = new_line[:(self.width - 3)] + "..."
            new_lines.append(new_line)
        return "\n".join(new_lines)

    def _print_error(self, cell):
        print("\n" + "=" * self.width)
        print("The following cell failed:\n")
        print(self._indent(cell.source))
        print("\nThe error was:\n")
        if cell.cell_type == "code":
            for output in cell.outputs:
                if output.output_type == "error":
                    print(self._indent("\n".join(output.traceback)))
        else:
            print(self._indent("You did not provide a response."))
        print

    def _print_pass(self, cell):
        print("\n" + "=" * self.width)
        print("The following cell passed:\n")
        print(self._indent(cell.source))
        print

    def _print_changed(self, cell):
        print("\n" + "=" * self.width)
        print("The following cell has changed:\n")
        print(self._indent(cell.source))
        print

    def preprocess(self, nb, resources):
        resources['nbgrader']['failed_cells'] = []
        resources['nbgrader']['passed_cells'] = []
        resources['nbgrader']['checksum_mismatch'] = []
        nb, resources = super(DisplayAutoGrades, self).preprocess(nb, resources)

        num_changed = len(resources['nbgrader']['checksum_mismatch'])
        num_failed = len(resources['nbgrader']['failed_cells'])
        num_passed = len(resources['nbgrader']['passed_cells'])

        if not self.ignore_checksums and num_changed > 0:
            print(fill(
                self.changed_warning.format(num_changed=num_changed),
                width=self.width))

            for cell_index in resources['nbgrader']['checksum_mismatch']:
                self._print_changed(nb.cells[cell_index])

        elif not self.invert:
            if num_failed == 0:
                print("Success! Your notebook passes all the tests.")

            else:
                print(fill(
                    self.failed_warning.format(num_failed=num_failed),
                    width=self.width))

                for cell_index in resources["nbgrader"]["failed_cells"]:
                    self._print_error(nb.cells[cell_index])

        else:
            if num_passed == 0:
                print("Success! The notebook does not pass any tests.")

            else:
                print(fill(
                    self.passed_warning.format(num_passed=num_passed),
                    width=self.width))

                for cell_index in resources["nbgrader"]["passed_cells"]:
                    self._print_pass(nb.cells[cell_index])

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
                resources['nbgrader']['checksum_mismatch'].append(cell_index)

        # if it's a grade cell, the add a grade
        if utils.is_grade(cell):
            score, max_score = utils.determine_grade(cell)

            # it's a markdown cell, so we can't do anything
            if score is None:
                pass
            elif score < max_score:
                resources['nbgrader']['failed_cells'].append(cell_index)
            else:
                resources['nbgrader']['passed_cells'].append(cell_index)

        return cell, resources
