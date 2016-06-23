from traitlets import Dict, Unicode, Bool
from textwrap import dedent

from .. import utils
from . import NbGraderPreprocessor


class ClearSolutions(NbGraderPreprocessor):

    code_stub = Dict(
        dict(python="# YOUR CODE HERE\nraise NotImplementedError()"),
        config=True,
        help="The code snippet that will replace code solutions")

    text_stub = Unicode(
        "YOUR ANSWER HERE",
        config=True,
        help="The text snippet that will replace written solutions")

    begin_solution_delimeter = Dict(
        dict(python="### BEGIN SOLUTION"),
        config=True,
        help="The delimiter marking the beginning of a solution")

    end_solution_delimeter = Dict(
        dict(python="### END SOLUTION"),
        config=True,
        help="The delimiter marking the end of a solution")

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

    def _config_changed(self, name, old, new):
        def check(x):
            if x in new.ClearSolutions:
                if not isinstance(new.ClearSolutions[x], dict):
                    return True
            return False

        def fix(new, x):
            self.log.warn(
                "The ClearSolutions.{var} option must now be given as a "
                "dictionary with keys for the language of the notebook. I will "
                "automatically convert ClearSolutions.{var} to a dictionary "
                "with a key for 'python', but note that this functionality may "
                "be removed in future releases.".format(var=x))
            new.ClearSolutions[x] = dict(python=new.ClearSolutions[x])
            return new

        if check('code_stub'):
            fix(new, 'code_stub')
        if check('begin_solution_delimeter'):
            fix(new, 'begin_solution_delimeter')
        if check('end_solution_delimeter'):
            fix(new, 'end_solution_delimeter')

        super(ClearSolutions, self)._config_changed(name, old, new)

    def _replace_solution_region(self, cell, language):
        """Find a region in the cell that is delimeted by
        `self.begin_solution_delimeter` and `self.end_solution_delimeter` (e.g.
        ### BEGIN SOLUTION and ### END SOLUTION). Replace that region either
        with the code stub or text stub, depending the cell type.

        This modifies the cell in place, and then returns True if a
        solution region was replaced, and False otherwise.

        """
        # pull out the cell input/source
        lines = cell.source.split("\n")
        if cell.cell_type == "code":
            stub_lines = self.code_stub[language].split("\n")
        else:
            stub_lines = self.text_stub.split("\n")

        new_lines = []
        in_solution = False
        replaced_solution = False
        begin = self.begin_solution_delimeter[language]
        end = self.end_solution_delimeter[language]

        for line in lines:
            # begin the solution area
            if line.strip() == begin:

                # check to make sure this isn't a nested BEGIN
                # SOLUTION region
                if in_solution:
                    raise RuntimeError(
                        "encountered nested begin solution statements")

                in_solution = True
                replaced_solution = True

                # replace it with the stub, indented as necessary
                indent = line[:line.find(begin)]
                for stub_line in stub_lines:
                    new_lines.append(indent + stub_line)

            # end the solution area
            elif line.strip() == end:
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
        language = nb.metadata.get("kernelspec", {}).get("language", "python")
        if language not in self.code_stub:
            raise ValueError(
                "language '{}' has not been specified in "
                "ClearSolutions.code_stub".format(language))
        if language not in self.begin_solution_delimeter:
            raise ValueError(
                "language '{}' has not been specified in "
                "ClearSolutions.begin_solution_delimeter".format(language))
        if language not in self.end_solution_delimeter:
            raise ValueError(
                "language '{}' has not been specified in "
                "ClearSolutions.end_solution_delimeter".format(language))

        resources["language"] = language
        nb, resources = super(ClearSolutions, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # replace solution regions with the relevant stubs
        language = resources["language"]
        replaced_solution = self._replace_solution_region(cell, language)

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
                cell.source = self.code_stub[language]
            else:
                cell.source = self.text_stub

        return cell, resources
