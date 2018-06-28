import re

from traitlets import Bool, Unicode
from textwrap import dedent

from . import NbGraderPreprocessor
from .. import utils


class ClearMarkScheme(NbGraderPreprocessor):

    begin_mark_scheme_delimeter = Unicode(
        "BEGIN MARK SCHEME",
        help="The delimiter marking the beginning of hidden tests cases"
    ).tag(config=True)

    end_mark_scheme_delimeter = Unicode(
        "END MARK SCHEME",
        help="The delimiter marking the end of hidden tests cases"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing marking scheme regions
            are not marked as task cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    def _remove_mark_scheme_region(self, cell):
        """Find a region in the cell that is delimeted by
        `self.begin_mark_scheme_delimeter` and `self.end_mark_scheme_delimeter` (e.g.  ###
        BEGIN MARK SCHEME and ### END MARK SCHEME). Remove that region
        depending the cell type.

        This modifies the cell in place, and then returns True if a
        mark region was removed, and False otherwise.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        in_ms = False
        removed_ms = False

        for line in lines:
            # begin the test area
            if self.begin_mark_scheme_delimeter in line:

                # check to make sure this isn't a nested BEGIN HIDDEN TESTS
                # region
                if in_ms:
                    raise RuntimeError(
                        "Encountered nested begin mark scheme statements")
                in_ms = True
                removed_ms = True

            # end the solution area
            elif self.end_mark_scheme_delimeter in line:
                in_ms = False

            # add lines as long as it's not in the hidden tests region
            elif not in_ms:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END HIDDEN TESTS statment
        if in_ms:
            raise RuntimeError("No end mark scheme tests statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return removed_ms

    def preprocess(self, nb, resources):
        nb, resources = super(ClearMarkScheme, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # remove hidden test regions
        removed_ms = self._remove_mark_scheme_region(cell)

        # determine whether the cell is a task cell
        is_task = utils.is_task(cell)

        # check that it is marked as a task cell if we remove a mark scheme
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_task and removed_ms:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Mark scheme region detected in a non-grade cell; "
                    "please make sure all mark scheme regions are within "
                    "'Manually graded task' cells."
                )

        return cell, resources
