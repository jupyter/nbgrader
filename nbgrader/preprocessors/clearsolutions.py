from traitlets import Unicode, Bool
from textwrap import dedent

from .. import utils
from . import NbGraderPreprocessor


class ClearSolutions(NbGraderPreprocessor):

    code_stub = Unicode(
        "# YOUR CODE HERE\nraise NotImplementedError()",
        config=True,
        help="The code snippet that will replace code solutions")

    text_stub = Unicode(
        "YOUR ANSWER HERE",
        config=True,
        help="The text snippet that will replace written solutions")

    comment_mark = Unicode(
        "#",
        config=True,
        help="The comment mark to prefix solution delimiters")

    begin_solution_delimeter = Unicode(
        "## BEGIN SOLUTION",
        config=True,
        help="The delimiter marking the beginning of a solution (excluding comment mark)")

    end_solution_delimeter = Unicode(
        "## END SOLUTION",
        config=True,
        help="The delimiter marking the end of a solution (excluding comment mark)")

    enforce_metadata = Bool(
        True,
        config=True,
        help=dedent(
            """
            Whether or not to complain if cells containing solutions regions are
            not marked as solution cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    )

    @property
    def begin_solution(self):
        return "{}{}".format(self.comment_mark, self.begin_solution_delimeter)

    @property
    def end_solution(self):
        return "{}{}".format(self.comment_mark, self.end_solution_delimeter)

    def _replace_solution_region(self, cell):
        """Find a region in the cell that is delimeted by
        `self.begin_solution` and `self.end_solution` (e.g. ### BEGIN
        SOLUTION and ### END SOLUTION). Replace that region either
        with the code stub or text stub, depending the cell type.

        This modifies the cell in place, and then returns True if a
        solution region was replaced, and False otherwise.

        """
        # pull out the cell input/source
        lines = cell.source.split("\n")
        if cell.cell_type == "code":
            stub_lines = self.code_stub.split("\n")
        else:
            stub_lines = self.text_stub.split("\n")

        new_lines = []
        in_solution = False
        replaced_solution = False

        for line in lines:
            # begin the solution area
            if line.strip() == self.begin_solution:

                # check to make sure this isn't a nested BEGIN
                # SOLUTION region
                if in_solution:
                    raise RuntimeError(
                        "encountered nested begin solution statements")

                in_solution = True
                replaced_solution = True

                # replace it with the stub, indented as necessary
                indent = line[:line.find(self.begin_solution)]
                for stub_line in stub_lines:
                    new_lines.append(indent + stub_line)

            # end the solution area
            elif line.strip() == self.end_solution:
                in_solution = False

            # add lines as long as it's not in the solution area
            elif not in_solution:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END SOLUTION statment
        if in_solution:
            raise RuntimeError("no end solution statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return replaced_solution

    def preprocess(self, nb, resources):
        nb, resources = super(ClearSolutions, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # replace solution regions with the relevant stubs
        replaced_solution = self._replace_solution_region(cell)

        # determine whether the cell is a solution/grade cell
        is_solution = utils.is_solution(cell)

        # check that it is marked as a solution cell if we replaced a solution
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_solution and replaced_solution:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Solution region detected in a non-solution cell; please make sure "
                    "all solution regions are within solution cells."
                )

        # replace solution cells with the code/text stub -- but not if
        # we already replaced a solution region, because that means
        # there are parts of the cells that should be preserved
        if is_solution and not replaced_solution:
            if cell.cell_type == 'code':
                cell.source = self.code_stub
            else:
                cell.source = self.text_stub

        return cell, resources
