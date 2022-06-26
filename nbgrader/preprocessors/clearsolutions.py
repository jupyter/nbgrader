import re

from traitlets import Dict, Unicode, Bool, observe
from traitlets.config.loader import Config
from textwrap import dedent

from .. import utils
from . import NbGraderPreprocessor
from typing import Any, Tuple
from nbformat.notebooknode import NotebookNode
from nbconvert.exporters.exporter import ResourcesDict


class ClearSolutions(NbGraderPreprocessor):

    code_stub = Dict(
        dict(python="# YOUR CODE HERE\nraise NotImplementedError()",
             matlab="% YOUR CODE HERE\nerror('No Answer Given!')",
             octave="% YOUR CODE HERE\nerror('No Answer Given!')",
             sas="/* YOUR CODE HERE */\n %notImplemented;",
             java="// YOUR CODE HERE"),
        help="The code snippet that will replace code solutions"
    ).tag(config=True)

    text_stub = Unicode(
        "YOUR ANSWER HERE",
        help="The text snippet that will replace written solutions"
    ).tag(config=True)

    begin_solution_delimeter = Unicode(
        "BEGIN SOLUTION",
        help="The delimiter marking the beginning of a solution"
    ).tag(config=True)

    end_solution_delimeter = Unicode(
        "END SOLUTION",
        help="The delimiter marking the end of a solution"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing solutions regions are
            not marked as solution cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    def _load_config(self, cfg: Config, **kwargs: Any) -> None:
        if 'code_stub' in cfg.ClearSolutions:
            if not isinstance(cfg.ClearSolutions.code_stub, dict):
                self.log.warning(
                    "The ClearSolutions.code_stub option must now be given as a "
                    "dictionary with keys for the language of the notebook. I will "
                    "automatically convert ClearSolutions.code_stub to a dictionary "
                    "with a key for 'python', but note that this functionality may "
                    "be removed in future releases.")
                cfg.ClearSolutions.code_stub = dict(python=cfg.ClearSolutions.code_stub)

        if 'comment_mark' in cfg.ClearSolutions:
            self.log.warning(
                "The ClearSolutions.comment_mark config option is deprecated. "
                "Please include the comment mark in ClearSolutions.begin_solution_delimeter "
                "and ClearSolutions.end_solution_delimeter instead.")
            del cfg.ClearSolutions.comment_mark

        super(ClearSolutions, self)._load_config(cfg, **kwargs)

    def _replace_solution_region(self, cell: NotebookNode, language: str) -> bool:
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

        for line in lines:
            # begin the solution area
            if self.begin_solution_delimeter in line:

                # check to make sure this isn't a nested BEGIN
                # SOLUTION region
                if in_solution:
                    self.log.error("Encountered nested begin solution statements. Cell contents are: \n%s", cell.source)
                    raise RuntimeError(
                        "encountered nested begin solution statements")

                in_solution = True
                replaced_solution = True

                # replace it with the stub, indented as necessary
                indent = re.match(r"\s*", line).group(0)
                for stub_line in stub_lines:
                    new_lines.append(indent + stub_line)

            # end the solution area
            elif self.end_solution_delimeter in line:
                in_solution = False

            # add lines as long as it's not in the solution area
            elif not in_solution:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END SOLUTION statment
        if in_solution:
            self.log.error("No end solution statement found. Cell contents are: \n%s", cell.source)
            raise RuntimeError("no end solution statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return replaced_solution

    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        language = nb.metadata.get("kernelspec", {}).get("language", "python")
        if language not in self.code_stub:
            raise ValueError(
                "language '{}' has not been specified in "
                "ClearSolutions.code_stub".format(language))

        resources["language"] = language
        nb, resources = super(ClearSolutions, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        # replace solution regions with the relevant stubs
        orig_cell_source = cell.source
        language = resources["language"]
        replaced_solution = self._replace_solution_region(cell, language)

        # determine whether the cell is a solution/grade cell
        is_solution = utils.is_solution(cell)

        # check that it is marked as a solution cell if we replaced a solution
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_solution and replaced_solution:
            if self.enforce_metadata:
                self.log.error(
                    "Solution region detected in a non-solution cell; please make sure "
                    "all solution regions are within solution cells. Cell contents are: \n%s", orig_cell_source
                )
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
