import sys
from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from nbgrader import utils
from textwrap import fill, dedent

import re
ansi_escape = re.compile(r'\x1b[^m]*m')


class DisplayAutoGrades(Preprocessor):
    """Preprocessor for displaying the autograder grades"""

    indent = Unicode("    ", config=True)
    width = Integer(90, config=True)

    def _indent(self, val):
        lines = val.split("\n")
        new_lines = []
        for line in lines:
            new_line = ansi_escape.sub('', self.indent + line)
            if len(new_line) > (self.width - 3):
                new_line = new_line[:(self.width - 3)] + "..."
            new_lines.append(new_line)
        return "\n".join(new_lines)

    def _print_error(self, cell):
        print("\n" + "=" * self.width)
        print("The following cell failed:\n")
        print(self._indent(cell.source))
        print("\nThe error was:\n")
        for output in cell.outputs:
            if output.output_type == "error":
                print self._indent("\n".join(output.traceback))
        print

    def preprocess(self, nb, resources):
        resources['nbgrader']['failed_cells'] = []
        nb, resources = super(DisplayAutoGrades, self).preprocess(nb, resources)

        if len(resources['nbgrader']['failed_cells']) == 0:
            print("Success! Your notebook passes all the tests.")

        else:
            print(fill(dedent(
                """
                VALIDATION FAILED ON {} CELLS! If you submit your assignment as
                it is, you WILL NOT receive full credit.
                """.format(len(resources['nbgrader']['failed_cells']))
            ).strip(), width=self.width))

            for cell_index in resources["nbgrader"]["failed_cells"]:
                self._print_error(nb.cells[cell_index])

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # if it's a grade cell, the add a grade
        if not utils.is_grade(cell):
            return cell, resources

        score, max_score = utils.determine_grade(cell)

        # it's a markdown cell, so we can't do anything
        if score is None:
            pass
        elif score < max_score:
            resources['nbgrader']['failed_cells'].append(cell_index)

        return cell, resources
